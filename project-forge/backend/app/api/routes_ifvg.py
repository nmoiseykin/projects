"""iFVG Reversal strategy API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.core.db import get_db
from app.core.config import settings
from app.models.ifvg import (
    IFVGBacktestRequest,
    IFVGResultsResponse,
    IFVGResult,
    IFVGResultKPIs
)
from app.models.backtest import BacktestRunResponse, BacktestRunStatus, RunStatus
from app.models.orm import BacktestRun, BacktestScenario, BacktestResult, StrategyRequest
from app.services.runner import run_backtest_run
from app.services.results import get_results_by_run
from app.core.logging import logger

router = APIRouter(prefix="/ifvg", tags=["ifvg"])


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """Verify API key (simple dev implementation)."""
    if settings.API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            logger.warning(f"Invalid API key attempt. Expected: {settings.API_KEY[:10]}..., Got: {x_api_key[:10] if x_api_key else 'None'}...")
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.post("/backtests", response_model=BacktestRunResponse)
async def create_ifvg_backtest(
    request: IFVGBacktestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Create a new iFVG backtest run."""
    try:
        # Create run with strategy_type='ifvg'
        run = BacktestRun(
            status="pending",
            total_scenarios=len(request.scenarios),
            strategy_type="ifvg"
        )
        db.add(run)
        await db.flush()
        
        # Create scenarios with strategy_type='ifvg'
        scenarios = []
        for scenario_params in request.scenarios:
            scenario = BacktestScenario(
                run_id=run.id,
                params=scenario_params.model_dump(),
                status="pending",
                strategy_type="ifvg"
            )
            db.add(scenario)
            scenarios.append(scenario)
        
        # Save strategy request if provided
        if request.strategy_text:
            strategy_request = StrategyRequest(
                run_id=run.id,
                request_text=request.strategy_text,
                mode=request.mode or "ifvg"
            )
            db.add(strategy_request)
        
        await db.commit()
        
        logger.info(f"Created iFVG backtest run {run.id} with {len(scenarios)} scenarios")
        
        # Start background task
        background_tasks.add_task(run_backtest_run_task, str(run.id))
        
        return BacktestRunResponse(
            run_id=str(run.id),
            status=RunStatus.PENDING,
            total_scenarios=len(scenarios),
            created_at=run.created_at
        )
    except Exception as e:
        logger.error(f"Error creating iFVG backtest run: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create iFVG backtest run: {str(e)}"
        )


@router.get("/backtests/{run_id}/status", response_model=BacktestRunStatus)
async def get_ifvg_backtest_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get status of an iFVG backtest run."""
    try:
        run_uuid = UUID(run_id)
        result = await db.execute(select(BacktestRun).where(BacktestRun.id == run_uuid))
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.strategy_type != "ifvg":
            raise HTTPException(status_code=400, detail="Run is not an iFVG strategy")
        
        return BacktestRunStatus(
            run_id=str(run.id),
            status=run.status,
            total_scenarios=run.total_scenarios,
            completed_scenarios=run.completed_scenarios,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
            strategy_type="ifvg"
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"Error getting iFVG backtest status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backtest status: {str(e)}"
        )


@router.get("/backtests/{run_id}/results", response_model=IFVGResultsResponse)
async def get_ifvg_backtest_results(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get results of an iFVG backtest run."""
    try:
        run_uuid = UUID(run_id)
        result = await db.execute(select(BacktestRun).where(BacktestRun.id == run_uuid))
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.strategy_type != "ifvg":
            raise HTTPException(status_code=400, detail="Run is not an iFVG strategy")
        
        # Reuse existing results fetching logic
        results_data = await get_results_by_run(db, run_uuid, strategy_type="ifvg")
        
        # Convert to iFVG result format
        ifvg_results = []
        for result_data in results_data:
            kpis_data = result_data.get("kpis", {})
            kpis = IFVGResultKPIs(
                total_trades=kpis_data.get("total_trades", 0),
                wins=kpis_data.get("wins", 0),
                losses=kpis_data.get("losses", 0),
                timeouts=kpis_data.get("timeouts", 0),
                win_rate_percent=kpis_data.get("win_rate_percent", 0.0),
                avg_fvg_size=kpis_data.get("avg_fvg_size"),
                avg_tp_pts=kpis_data.get("avg_tp_pts"),
                avg_sl_pts=kpis_data.get("avg_sl_pts"),
                expectancy_r=kpis_data.get("expectancy_r"),
                profit_factor=kpis_data.get("profit_factor")
            )
            
            ifvg_result = IFVGResult(
                id=str(result_data.get("id", "")),
                scenario_id=str(result_data.get("scenario_id", "")),
                grouping=result_data.get("grouping"),
                totals=result_data.get("totals"),
                kpis=kpis,
                created_at=result_data.get("created_at")
            )
            ifvg_results.append(ifvg_result)
        
        return IFVGResultsResponse(
            run_id=run_id,
            results=ifvg_results,
            total_results=len(ifvg_results)
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"Error getting iFVG backtest results: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backtest results: {str(e)}"
        )


@router.get("/backtests/{run_id}/trades")
async def get_ifvg_trades_for_group(
    run_id: str,
    fvg_timeframe: Optional[str] = None,
    entry_timeframe: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day_of_week: Optional[int] = None,
    direction: Optional[str] = None,
    use_adaptive_rr: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """
    Get iFVG trades filtered by grouping criteria.
    Re-generates trades for matching scenarios and filters by the provided criteria.
    """
    try:
        logger.info(f"Getting trades for run {run_id} with filters: fvg_tf={fvg_timeframe}, entry_tf={entry_timeframe}, year={year}, month={month}, dow={day_of_week}, dir={direction}, adaptive={use_adaptive_rr}")
        
        run_uuid = UUID(run_id)
        result = await db.execute(select(BacktestRun).where(BacktestRun.id == run_uuid))
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.strategy_type != "ifvg":
            raise HTTPException(status_code=400, detail="Run is not an iFVG strategy")
        
        # Get all scenarios for this run
        scenarios_stmt = select(BacktestScenario).where(BacktestScenario.run_id == run_uuid)
        scenarios_result = await db.execute(scenarios_stmt)
        scenarios = list(scenarios_result.scalars().all())
        
        logger.info(f"Found {len(scenarios)} total scenarios for run {run_id}")
        
        if not scenarios:
            logger.warning(f"No scenarios found for run {run_id}")
            return {"trades": [], "count": 0}
        
        # Filter scenarios by fvg_timeframe, entry_timeframe, use_adaptive_rr
        matching_scenarios = []
        for scenario in scenarios:
            params = scenario.params
            scenario_fvg_tf = params.get('fvg_timeframe')
            scenario_entry_tf = params.get('entry_timeframe')
            scenario_adaptive = params.get('use_adaptive_rr')
            
            # Normalize boolean values for comparison
            if isinstance(scenario_adaptive, str):
                scenario_adaptive = scenario_adaptive.lower() == 'true'
            if isinstance(use_adaptive_rr, str):
                use_adaptive_rr_bool = use_adaptive_rr.lower() == 'true'
            else:
                use_adaptive_rr_bool = use_adaptive_rr
            
            if fvg_timeframe and scenario_fvg_tf != fvg_timeframe:
                logger.debug(f"Scenario {scenario.id} skipped: fvg_tf mismatch ({scenario_fvg_tf} != {fvg_timeframe})")
                continue
            if entry_timeframe and scenario_entry_tf != entry_timeframe:
                logger.debug(f"Scenario {scenario.id} skipped: entry_tf mismatch ({scenario_entry_tf} != {entry_timeframe})")
                continue
            if use_adaptive_rr_bool is not None and bool(scenario_adaptive) != bool(use_adaptive_rr_bool):
                logger.debug(f"Scenario {scenario.id} skipped: adaptive_rr mismatch ({scenario_adaptive} != {use_adaptive_rr_bool})")
                continue
            matching_scenarios.append(scenario)
            logger.debug(f"Scenario {scenario.id} matches filters")
        
        logger.info(f"Found {len(matching_scenarios)} matching scenarios")
        
        if not matching_scenarios:
            logger.warning(f"No scenarios match filters: fvg_tf={fvg_timeframe}, entry_tf={entry_timeframe}, adaptive={use_adaptive_rr}")
            return {"trades": [], "count": 0}
        
        # Generate trades for all matching scenarios
        from app.services.ifvg_runner import generate_ifvg_trades_only
        from datetime import datetime, date
        all_trades = []
        
        logger.info(f"Found {len(matching_scenarios)} matching scenarios for filters: fvg_tf={fvg_timeframe}, entry_tf={entry_timeframe}, adaptive_rr={use_adaptive_rr}")
        
        logger.info(f"Applying date/direction filters: year={year}, month={month}, day_of_week={day_of_week}, direction={direction}")
        
        for scenario in matching_scenarios:
            try:
                # Pass filters to generate_ifvg_trades_only - it will filter at SQL level and early in pipeline
                trades = await generate_ifvg_trades_only(
                    db, 
                    scenario,
                    filter_year=year,
                    filter_month=month,
                    filter_day_of_week=day_of_week,
                    filter_direction=direction
                )
                logger.info(f"Generated {len(trades)} trades for scenario {scenario.id} (with filters applied)")
                all_trades.extend(trades)
            except Exception as e:
                logger.warning(f"Error generating trades for scenario {scenario.id}: {e}", exc_info=True)
                continue
        
        logger.info(f"Total trades generated (already filtered): {len(all_trades)}")
        
        # Convert datetime objects to strings for JSON serialization
        filtered_trades = []
        for trade in all_trades:
            trade_dict = {
                'trading_date': trade['trading_date'].isoformat() if hasattr(trade['trading_date'], 'isoformat') else str(trade['trading_date']),
                'entry_time': trade['entry_ts'].time().isoformat() if hasattr(trade['entry_ts'], 'time') else str(trade.get('entry_ts', '')),
                'entry_price': trade['entry_price'],
                'target_price': trade['take_profit'],
                'stop_price': trade['stop_loss'],
                'direction': trade['direction'],
                'outcome': trade['outcome'],
                'exit_time': trade['exit_ts'].isoformat() if trade['exit_ts'] and hasattr(trade['exit_ts'], 'isoformat') else (str(trade['exit_ts']) if trade['exit_ts'] else None),
                'exit_price': trade['exit_price'],
                'fvg_timestamp': trade['fvg_ts'].isoformat() if hasattr(trade['fvg_ts'], 'isoformat') else str(trade['fvg_ts']),
                'fvg_direction': trade['fvg_direction'],
                'gap_low': trade['gap_low'],
                'gap_high': trade['gap_high'],
                'fvg_size': trade['fvg_size'],
                'inversion_timestamp': trade['inv_ts'].isoformat() if hasattr(trade['inv_ts'], 'isoformat') else str(trade['inv_ts']),
                'inversion_open_price': trade.get('inv_open_price'),
                'inversion_close_price': trade.get('inv_close_price'),
                'use_adaptive_rr': trade['use_adaptive_rr']
            }
            filtered_trades.append(trade_dict)
        
        logger.info(f"Returning {len(filtered_trades)} trades")
        
        return {"trades": filtered_trades, "count": len(filtered_trades)}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"Error getting iFVG trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trades: {str(e)}"
        )


async def run_backtest_run_task(run_id: str):
    """Background task to run iFVG backtest."""
    from app.core.db import AsyncSessionLocal
    from uuid import UUID
    
    async with AsyncSessionLocal() as session:
        try:
            await run_backtest_run(session, UUID(run_id))
        except Exception as e:
            logger.error(f"Background task failed for iFVG run {run_id}: {e}", exc_info=True)

