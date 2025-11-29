"""Daily Scorecard strategy API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.core.db import get_db
from app.core.config import settings
from app.models.daily_scorecard import (
    DailyScorecardBacktestRequest,
    DailyScorecardResultsResponse,
    DailyScorecardResult,
    DailyScorecardWeeklyStats,
    DailyScorecardDailyStats
)
from app.models.backtest import BacktestRunResponse, BacktestRunStatus, RunStatus
from app.models.orm import BacktestRun, BacktestScenario, BacktestResult, StrategyRequest
from app.services.runner import run_backtest_run
from app.services.results import get_results_by_run
from app.core.logging import logger
from datetime import datetime

router = APIRouter(prefix="/daily-scorecard", tags=["daily-scorecard"])


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    """Verify API key (simple dev implementation)."""
    if settings.API_KEY:
        if not x_api_key or x_api_key != settings.API_KEY:
            logger.warning(f"Invalid API key attempt. Expected: {settings.API_KEY[:10]}..., Got: {x_api_key[:10] if x_api_key else 'None'}...")

    return True


async def run_backtest_run_task(run_id: str):
    """Background task to run backtest."""
    from app.core.db import AsyncSessionLocal
    from uuid import UUID
    async with AsyncSessionLocal() as session:
        try:
            await run_backtest_run(session, UUID(run_id))
        except Exception as e:
            logger.error(f"Error in backtest run task {run_id}: {e}", exc_info=True)


@router.post("/backtests", response_model=BacktestRunResponse)
async def create_daily_scorecard_backtest(
    request: DailyScorecardBacktestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Create a new Daily Scorecard backtest run."""
    try:
        # Create run with strategy_type='daily_scorecard'
        run = BacktestRun(
            status="pending",
            total_scenarios=len(request.scenarios),
            strategy_type="daily_scorecard"
        )
        db.add(run)
        await db.flush()
        
        # Create scenarios with strategy_type='daily_scorecard'
        scenarios = []
        for scenario_params in request.scenarios:
            scenario = BacktestScenario(
                run_id=run.id,
                params=scenario_params.model_dump(),
                status="pending",
                strategy_type="daily_scorecard"
            )
            db.add(scenario)
            scenarios.append(scenario)
        
        # Save strategy request if provided
        if request.strategy_text:
            strategy_request = StrategyRequest(
                run_id=run.id,
                request_text=request.strategy_text,
                mode=request.mode or "daily_scorecard"
            )
            db.add(strategy_request)
        
        await db.commit()
        
        logger.info(f"Created Daily Scorecard backtest run {run.id} with {len(scenarios)} scenarios")
        
        # Start background task
        background_tasks.add_task(run_backtest_run_task, str(run.id))
        
        return BacktestRunResponse(
            run_id=str(run.id),
            status=RunStatus.PENDING,
            total_scenarios=len(scenarios),
            created_at=run.created_at
        )
    except Exception as e:
        logger.error(f"Error creating Daily Scorecard backtest run: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Daily Scorecard backtest run: {str(e)}"
        )


@router.get("/backtests/{run_id}/status", response_model=BacktestRunStatus)
async def get_daily_scorecard_backtest_status(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get status of a Daily Scorecard backtest run."""
    try:
        run_uuid = UUID(run_id)
        result = await db.execute(select(BacktestRun).where(BacktestRun.id == run_uuid))
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.strategy_type != "daily_scorecard":
            raise HTTPException(status_code=400, detail="Run is not a Daily Scorecard strategy")
        
        return BacktestRunStatus(
            run_id=str(run.id),
            status=run.status,
            total_scenarios=run.total_scenarios,
            completed_scenarios=run.completed_scenarios,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
            strategy_type="daily_scorecard"
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"Error getting Daily Scorecard backtest status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backtest status: {str(e)}"
        )


@router.get("/backtests/{run_id}/results", response_model=DailyScorecardResultsResponse)
async def get_daily_scorecard_results(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get results of a Daily Scorecard backtest run."""
    try:
        run_uuid = UUID(run_id)
        result = await db.execute(select(BacktestRun).where(BacktestRun.id == run_uuid))
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Backtest run not found")
        
        if run.strategy_type != "daily_scorecard":
            raise HTTPException(status_code=400, detail="Run is not a Daily Scorecard strategy")
        
        # Get results
        results_data = await get_results_by_run(db, run.id, strategy_type="daily_scorecard")
        
        # Convert to Daily Scorecard result format
        daily_scorecard_results = []
        for result_data in results_data:
            # The result_data contains grouping with Daily Scorecard data
            grouping = result_data.get('grouping', {})
            if not grouping.get('weekly_stats') or not grouping.get('daily_stats'):
                continue
            
            weekly_stats = grouping['weekly_stats']
            daily_stats = grouping['daily_stats']
            
            # Convert daily_stats to model format
            daily_stats_models = [
                DailyScorecardDailyStats(**ds) for ds in daily_stats
            ]
            
            daily_scorecard_results.append(
                DailyScorecardResult(
                    id=str(result_data.get('id', '')),
                    scenario_id=str(result_data.get('scenario_id', '')),
                    calendar_week=grouping.get('calendar_week', 0),
                    year_start=grouping.get('year_start', 2020),
                    year_end=grouping.get('year_end', 2025),
                    weekly_stats=DailyScorecardWeeklyStats(**weekly_stats),
                    daily_stats=daily_stats_models,
                    created_at=result_data.get('created_at', datetime.now())
                )
            )
        
        return DailyScorecardResultsResponse(
            run_id=str(run.id),
            results=daily_scorecard_results,
            total_results=len(daily_scorecard_results)
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"Error getting Daily Scorecard results: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get results: {str(e)}"
        )

