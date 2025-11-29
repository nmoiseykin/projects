"""Backtest API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.db import get_db
from app.core.config import settings
from app.models.backtest import (
    BacktestRequest,
    BacktestRunResponse,
    BacktestRunStatus,
    BacktestResultsResponse,
    BacktestResult,
    RunStatus
)
from app.models.orm import BacktestRun, BacktestScenario, StrategyRequest
from app.services.runner import run_backtest_run
from app.services.results import get_results_by_run
from app.core.logging import logger

router = APIRouter(prefix="/backtests", tags=["backtests"])


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """Verify API key (simple dev implementation)."""
    if settings.API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            logger.warning(f"Invalid API key attempt. Expected: {settings.API_KEY[:10]}..., Got: {x_api_key[:10] if x_api_key else 'None'}...")
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.post("", response_model=BacktestRunResponse)
async def create_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Create a new backtest run."""
    try:
        # Create run
        run = BacktestRun(
            status="pending",
            total_scenarios=len(request.scenarios)
        )
        db.add(run)
        await db.flush()
        
        # Create scenarios
        scenarios = []
        for scenario_params in request.scenarios:
            scenario = BacktestScenario(
                run_id=run.id,
                params=scenario_params.model_dump(),
                status="pending"
            )
            db.add(scenario)
            scenarios.append(scenario)
        
        # Save strategy request if provided
        if request.strategy_text:
            strategy_request = StrategyRequest(
                run_id=run.id,
                request_text=request.strategy_text,
                mode=request.mode or "unknown"
            )
            db.add(strategy_request)
        
        await db.commit()
        
        logger.info(f"Created backtest run {run.id} with {len(scenarios)} scenarios")
        
        # Start background task
        background_tasks.add_task(run_backtest_run_task, str(run.id))
        
        return BacktestRunResponse(
            run_id=str(run.id),
            status=RunStatus.PENDING,
            total_scenarios=len(scenarios),
            created_at=run.created_at
        )
    except Exception as e:
        logger.error(f"Error creating backtest run: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backtest run: {str(e)}"
        )


async def run_backtest_run_task(run_id: str):
    """Background task to run backtest."""
    from app.core.db import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            await run_backtest_run(session, UUID(run_id))
        except Exception as e:
            logger.error(f"Background task failed for run {run_id}: {e}")


@router.get("", response_model=List[BacktestRunStatus])
async def list_backtest_runs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """List all backtest runs (most recent first)."""
    try:
        from sqlalchemy import desc
        
        logger.info(f"Listing backtest runs (limit={limit})")
        
        stmt = (
            select(BacktestRun)
            .order_by(desc(BacktestRun.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        runs = result.scalars().all()
        logger.info(f"Found {len(runs)} runs")
        
        if not runs:
            return []
        
        # Fetch strategy requests for all runs
        run_ids = [run.id for run in runs]
        stmt_strategies = select(StrategyRequest).where(StrategyRequest.run_id.in_(run_ids))
        result_strategies = await db.execute(stmt_strategies)
        strategies = {str(s.run_id): s for s in result_strategies.scalars().all()}
        logger.info(f"Found {len(strategies)} strategy requests")
        
        # Fetch first scenario for each run to get parameters
        stmt_scenarios = select(BacktestScenario).where(BacktestScenario.run_id.in_(run_ids))
        result_scenarios = await db.execute(stmt_scenarios)
        all_scenarios = result_scenarios.scalars().all()
        logger.info(f"Found {len(all_scenarios)} scenarios")
        
        # Group scenarios by run_id, take first one for each run
        scenarios_by_run = {}
        for scenario in all_scenarios:
            run_id_str = str(scenario.run_id)
            if run_id_str not in scenarios_by_run:
                scenarios_by_run[run_id_str] = scenario
        
        # WIN RATE CALCULATION - COMMENTED OUT (was causing performance issues)
        results_by_run = {}  # Empty dict to avoid errors
    
        results = []
        for run in runs:
            try:
                # Try to convert status to RunStatus enum, fallback to pending if invalid
                try:
                    status = RunStatus(run.status)
                except ValueError:
                    # Handle invalid status values (e.g., 'cancelled' before enum was updated)
                    if run.status == 'cancelled':
                        status = RunStatus.CANCELLED
                    else:
                        logger.warning(f"Invalid run status '{run.status}' for run {run.id}, defaulting to pending")
                        status = RunStatus.PENDING
                
                scenario = scenarios_by_run.get(str(run.id))
                scenario_params = scenario.params if scenario else None
                
                # WIN RATE CALCULATION - COMMENTED OUT
                overall_win_rate = None
                
                # Safely get strategy info
                strategy = strategies.get(str(run.id))
                strategy_text = strategy.request_text if strategy else None
                mode = strategy.mode if strategy else None
                
                results.append(BacktestRunStatus(
                    run_id=str(run.id),
                    status=status,
                    total_scenarios=run.total_scenarios,
                    completed_scenarios=run.completed_scenarios,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    created_at=run.created_at,
                    strategy_text=strategy_text,
                    mode=mode,
                    strategy_type=run.strategy_type,
                    scenario_params=scenario_params,
                    overall_win_rate=overall_win_rate
                ))
            except Exception as e:
                logger.error(f"Error processing run {run.id}: {e}", exc_info=True)
                # Skip this run but continue with others
                continue
        
        logger.info(f"Returning {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error in list_backtest_runs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backtest runs: {str(e)}"
        )


@router.get("/{run_id}", response_model=BacktestRunStatus)
async def get_backtest_status(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get backtest run status."""
    stmt = select(BacktestRun).where(BacktestRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Fetch strategy request
    stmt_strategy = select(StrategyRequest).where(StrategyRequest.run_id == run_id)
    result_strategy = await db.execute(stmt_strategy)
    strategy = result_strategy.scalar_one_or_none()
    
    # Fetch first scenario to get parameters (for display purposes)
    stmt_scenario = select(BacktestScenario).where(BacktestScenario.run_id == run_id).limit(1)
    result_scenario = await db.execute(stmt_scenario)
    first_scenario = result_scenario.scalar_one_or_none()
    scenario_params = first_scenario.params if first_scenario else None
    
    # WIN RATE CALCULATION - COMMENTED OUT
    # # Calculate overall win rate from all results for this run
    # overall_win_rate = None
    # if first_scenario:
    #     from app.models.orm import BacktestResult
    #     # Get all scenarios for this run
    #     stmt_all_scenarios = select(BacktestScenario).where(BacktestScenario.run_id == run_id)
    #     result_all_scenarios = await db.execute(stmt_all_scenarios)
    #     all_scenarios = result_all_scenarios.scalars().all()
    #     scenario_ids = [s.id for s in all_scenarios]
    #     
    #     if scenario_ids:
    #         # Get all results for these scenarios
    #         stmt_results = select(BacktestResult).where(BacktestResult.scenario_id.in_(scenario_ids))
    #         result_results = await db.execute(stmt_results)
    #         all_results = result_results.scalars().all()
    #         
    #         if all_results:
    #             total_trades = 0
    #             total_wins = 0
    #             for res in all_results:
    #                 totals = res.totals or {}
    #                 total_trades += totals.get('total_trades', 0)
    #                 total_wins += totals.get('wins', 0)
    #             
    #             if total_trades > 0:
    #                 overall_win_rate = round((total_wins / total_trades) * 100.0, 2)
    overall_win_rate = None
    
    # Handle status conversion with fallback for invalid values
    try:
        status = RunStatus(run.status)
    except ValueError:
        # Handle invalid status values (e.g., 'cancelled' before enum was updated)
        if run.status == 'cancelled':
            status = RunStatus.CANCELLED
        else:
            logger.warning(f"Invalid run status '{run.status}' for run {run.id}, defaulting to pending")
            status = RunStatus.PENDING
    
    return BacktestRunStatus(
        run_id=str(run.id),
        status=status,
        total_scenarios=run.total_scenarios,
        completed_scenarios=run.completed_scenarios,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
        strategy_text=strategy.request_text if strategy else None,
        mode=strategy.mode if strategy else None,
        strategy_type=run.strategy_type,
        scenario_params=scenario_params,
        overall_win_rate=overall_win_rate
    )


@router.get("/{run_id}/results", response_model=BacktestResultsResponse)
async def get_backtest_results(
    run_id: UUID,
    page: int = 1,
    page_size: int = 100,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get backtest results."""
    # Verify run exists
    stmt = select(BacktestRun).where(BacktestRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get results
    # Fetch all results (no pagination for now - get all pages)
    all_results = []
    current_page = 1
    while True:
        page_results = await get_results_by_run(db, run_id, current_page, page_size, run.strategy_type)
        if len(page_results) == 0:
            break
        all_results.extend(page_results)
        if len(page_results) < page_size:
            break
        current_page += 1
    
    total = len(all_results)
    orm_results = all_results[(page - 1) * page_size:page * page_size]
    
    # Get scenario params for each result
    # Note: all_results is a list of dictionaries from get_results_by_run
    scenario_ids = list(set([str(r.get("scenario_id")) for r in orm_results if r.get("scenario_id")]))
    if scenario_ids:
        stmt_scenarios = select(BacktestScenario).where(BacktestScenario.id.in_([UUID(sid) for sid in scenario_ids]))
        scenario_result = await db.execute(stmt_scenarios)
        scenarios = {str(s.id): s for s in scenario_result.scalars().all()}
    else:
        scenarios = {}
    
    # Convert to response models
    results = []
    for orm_result in orm_results:
        # Handle both dict and object access
        result_id = str(orm_result.get("id") if isinstance(orm_result, dict) else orm_result.id)
        scenario_id = str(orm_result.get("scenario_id") if isinstance(orm_result, dict) else orm_result.scenario_id)
        
        scenario = scenarios.get(scenario_id) if scenario_id else None
        scenario_params = scenario.params if scenario else {}
        
        # Add TP/SL to grouping for display (only for standard strategy)
        grouping = (orm_result.get("grouping") if isinstance(orm_result, dict) else orm_result.grouping) or {}
        
        # Only add scenario params to grouping for standard strategy (not iFVG)
        if scenario_params and run.strategy_type != 'ifvg':
            grouping = {
                **grouping,
                "target_pts": scenario_params.get("target_pts"),
                "stop_pts": scenario_params.get("stop_pts"),
                "entry_time_start": scenario_params.get("entry_time_start"),
                "entry_time_end": scenario_params.get("entry_time_end"),
                "trade_end_time": scenario_params.get("trade_end_time", "16:00:00")
            }
        
        results.append(BacktestResult(
            id=result_id,
            scenario_id=scenario_id,
            grouping=grouping,
            totals=(orm_result.get("totals") if isinstance(orm_result, dict) else orm_result.totals) or {},
            kpis=(orm_result.get("kpis") if isinstance(orm_result, dict) else orm_result.kpis) or {}
        ))
    
    return BacktestResultsResponse(
        run_id=str(run_id),
        results=results,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/results/{result_id}/trades")
async def get_result_trades(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get individual trades for a specific result."""
    from app.services.trades import get_trades_for_result
    
    try:
        trades = await get_trades_for_result(db, result_id)
        return {"trades": trades, "count": len(trades)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching trades for result {result_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching trades: {str(e)}")


@router.get("/running/status")
async def get_running_status(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get status of all running and pending backtest runs."""
    from sqlalchemy import text
    
    # Get running/pending runs
    stmt = select(BacktestRun).where(
        (BacktestRun.status == "running") | (BacktestRun.status == "pending")
    ).order_by(BacktestRun.created_at.desc())
    result = await db.execute(stmt)
    runs = result.scalars().all()
    
    # Check for long-running database queries
    query_stmt = text("""
        SELECT 
            pid,
            usename,
            application_name,
            state,
            query_start,
            NOW() - query_start AS duration,
            LEFT(query, 150) AS query_preview
        FROM pg_stat_activity
        WHERE state = 'active'
          AND query NOT LIKE '%pg_stat_activity%'
          AND query NOT LIKE '%pg_catalog%'
          AND pid != pg_backend_pid()
        ORDER BY query_start
    """)
    query_result = await db.execute(query_stmt)
    queries = query_result.fetchall()
    
    running_runs = [
        {
            "run_id": str(run.id),
            "status": run.status,
            "progress": f"{run.completed_scenarios}/{run.total_scenarios}",
            "completed_scenarios": run.completed_scenarios,
            "total_scenarios": run.total_scenarios,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
        }
        for run in runs
    ]
    
    active_queries = [
        {
            "pid": q[0],
            "duration_seconds": q[5].total_seconds() if q[5] else 0,
            "query_preview": q[6],
            "state": q[3],
        }
        for q in queries
    ]
    
    return {
        "running_runs": running_runs,
        "active_queries": active_queries,
        "total_running": len(running_runs),
        "total_queries": len(active_queries),
    }


@router.post("/{run_id}/cancel")
async def cancel_backtest_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Cancel a running or pending backtest run."""
    stmt = select(BacktestRun).where(BacktestRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.status not in ["running", "pending"]:
        raise HTTPException(
            status_code=400,
            detail=f"Run is {run.status}, cannot cancel. Only 'running' or 'pending' runs can be cancelled."
        )
    
    # Mark run as cancelled
    run.status = "cancelled"
    run.finished_at = datetime.utcnow()
    
    # Mark all pending/running scenarios as cancelled
    stmt_scenarios = select(BacktestScenario).where(
        BacktestScenario.run_id == run_id,
        BacktestScenario.status.in_(["pending", "running"])
    )
    result_scenarios = await db.execute(stmt_scenarios)
    scenarios = result_scenarios.scalars().all()
    
    for scenario in scenarios:
        scenario.status = "cancelled"
    
    await db.commit()
    
    logger.info(f"Cancelled backtest run {run_id} with {len(scenarios)} scenarios")
    
    return {
        "run_id": str(run_id),
        "status": "cancelled",
        "cancelled_scenarios": len(scenarios),
        "message": f"Run {run_id} and {len(scenarios)} scenarios cancelled"
    }


@router.post("/running/cancel-all")
async def cancel_all_running(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Cancel all running and pending backtest runs."""
    stmt = select(BacktestRun).where(
        (BacktestRun.status == "running") | (BacktestRun.status == "pending")
    )
    result = await db.execute(stmt)
    runs = result.scalars().all()
    
    if not runs:
        return {
            "cancelled_runs": 0,
            "cancelled_scenarios": 0,
            "message": "No running or pending runs to cancel"
        }
    
    cancelled_runs = []
    total_scenarios = 0
    
    for run in runs:
        run.status = "cancelled"
        run.finished_at = datetime.utcnow()
        
        # Mark all pending/running scenarios as cancelled
        stmt_scenarios = select(BacktestScenario).where(
            BacktestScenario.run_id == run.id,
            BacktestScenario.status.in_(["pending", "running"])
        )
        result_scenarios = await db.execute(stmt_scenarios)
        scenarios = result_scenarios.scalars().all()
        
        for scenario in scenarios:
            scenario.status = "cancelled"
        
        cancelled_runs.append(str(run.id))
        total_scenarios += len(scenarios)
    
    await db.commit()
    
    logger.info(f"Cancelled {len(runs)} runs with {total_scenarios} total scenarios")
    
    return {
        "cancelled_runs": len(runs),
        "cancelled_scenarios": total_scenarios,
        "run_ids": cancelled_runs,
        "message": f"Cancelled {len(runs)} runs and {total_scenarios} scenarios"
    }


@router.post("/queries/kill-all")
async def kill_all_queries(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Kill all active database queries (except this one)."""
    from sqlalchemy import text
    
    # Get all active queries
    query_stmt = text("""
        SELECT pid
        FROM pg_stat_activity
        WHERE state = 'active'
          AND query NOT LIKE '%pg_stat_activity%'
          AND query NOT LIKE '%pg_catalog%'
          AND pid != pg_backend_pid()
    """)
    result = await db.execute(query_stmt)
    pids = [row[0] for row in result.fetchall()]
    
    if not pids:
        return {
            "killed_queries": 0,
            "message": "No active queries to kill"
        }
    
    # Kill each query
    killed = []
    for pid in pids:
        try:
            kill_stmt = text(f"SELECT pg_terminate_backend({pid})")
            await db.execute(kill_stmt)
            killed.append(pid)
        except Exception as e:
            logger.warning(f"Failed to kill query {pid}: {e}")
    
    await db.commit()
    
    logger.info(f"Killed {len(killed)} database queries")
    
    return {
        "killed_queries": len(killed),
        "pids": killed,
        "message": f"Killed {len(killed)} active database queries"
    }

