"""Backtest runner - orchestrates SQL execution."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from typing import Dict, Any, List, Optional
from uuid import UUID
from app.models.orm import BacktestRun, BacktestScenario
from app.services.sql_templates import template_engine
from app.services.analyzer import calculate_kpis
from app.services.results import save_results
from app.services.tz import parse_time_string
from app.core.logging import logger
from app.core.db import AsyncSessionLocal


async def run_backtest_scenario(
    session: AsyncSession,
    scenario: BacktestScenario,
    grouping_type: str = "hierarchical"
) -> List[Dict[str, Any]]:
    """
    Execute a single backtest scenario.
    
    Args:
        session: Database session
        scenario: Scenario to execute
        grouping_type: Type of grouping ("by_year", "by_dow", "by_candle")
        
    Returns:
        List of result dictionaries
    """
    # Route by strategy_type
    strategy_type = scenario.strategy_type or 'standard'
    logger.info(f"Routing scenario {scenario.id}: strategy_type={strategy_type}, run_id={scenario.run_id}")
    
    if strategy_type == 'ifvg':
        logger.info(f"Executing iFVG scenario {scenario.id}")
        from app.services.ifvg_runner import run_ifvg_scenario
        return await run_ifvg_scenario(session, scenario, grouping_type)
    
    if strategy_type == 'daily_scorecard':
        logger.info(f"Executing Daily Scorecard scenario {scenario.id}")
        from app.services.daily_scorecard_runner import run_daily_scorecard_scenario
        return await run_daily_scorecard_scenario(session, scenario, grouping_type)
    
    # Standard strategy logic
    params = scenario.params
    
    # Prepare template parameters
    # Ensure trend_enabled is always a boolean (not None)
    trend_enabled_val = params.get("trend_enabled")
    if trend_enabled_val is None:
        trend_enabled_val = False
    else:
        trend_enabled_val = bool(trend_enabled_val)
    
    template_params = {
        "entry_time_start": parse_time_string(params["entry_time_start"]),
        "entry_time_end": parse_time_string(params["entry_time_end"]),
        "trade_end_time": parse_time_string(params.get("trade_end_time", "16:00:00")),  # Default 4pm
        "target_pts": float(params["target_pts"]),
        "stop_pts": float(params["stop_pts"]),
        "direction": params.get("direction"),
        "year_start": int(params["year_start"]),
        "year_end": int(params["year_end"]),
        # Trend filter parameters (with defaults if not present)
        "trend_enabled": trend_enabled_val,
        "trend_timeframe": params.get("trend_timeframe", "15m") if trend_enabled_val else "15m",
        "trend_period": int(params.get("trend_period", 20)) if trend_enabled_val else 20,
        "trend_type": params.get("trend_type", "sma") if trend_enabled_val else "sma",
        "trend_strict": params.get("trend_strict", True) if trend_enabled_val else True,
    }
    
    # Render SQL template
    if grouping_type == "hierarchical":
        sql = template_engine.render_hierarchical(template_params)
    elif grouping_type == "by_year":
        sql = template_engine.render_by_year(template_params)
    elif grouping_type == "by_dow":
        sql = template_engine.render_by_dow(template_params)
    elif grouping_type == "by_candle":
        sql = template_engine.render_by_candle(template_params)
    else:
        raise ValueError(f"Unknown grouping type: {grouping_type}")
    
    logger.info(f"Executing scenario {scenario.id} with grouping {grouping_type}")
    logger.debug(f"SQL query: {sql[:500]}...")  # Log first 500 chars of SQL
    
    # Execute SQL
    try:
        # Use a fresh connection/transaction for each query to avoid transaction issues
        result = await session.execute(text(sql))
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        results = []
        for row in rows:
            row_dict = dict(row._mapping)
            
            # Extract grouping info for hierarchical structure
            grouping = {
                "level": row_dict.get("level", "unknown"),
                "grouping_type": grouping_type
            }
            if "year" in row_dict and row_dict["year"] is not None:
                grouping["year"] = int(row_dict["year"])
            if "month" in row_dict and row_dict["month"] is not None:
                grouping["month"] = int(row_dict["month"])
            if "trading_date" in row_dict and row_dict["trading_date"] is not None:
                # Convert date to string format for JSON serialization
                if hasattr(row_dict["trading_date"], 'isoformat'):
                    grouping["trading_date"] = row_dict["trading_date"].isoformat()
                else:
                    grouping["trading_date"] = str(row_dict["trading_date"])
            if "direction" in row_dict:
                grouping["direction"] = row_dict["direction"]
            
            # Add strategy identifiers
            grouping["entry_time_start"] = template_params["entry_time_start"]
            grouping["entry_time_end"] = template_params["entry_time_end"]
            grouping["target_pts"] = template_params["target_pts"]
            grouping["stop_pts"] = template_params["stop_pts"]
            
            # Extract totals
            totals = {
                "total_trades": row_dict.get("total_trades", 0),
                "wins": row_dict.get("wins", 0),
                "losses": row_dict.get("losses", 0),
                "timeouts": row_dict.get("timeouts", 0)
            }
            
            # Calculate KPIs
            kpis = calculate_kpis(
                totals["total_trades"],
                totals["wins"],
                totals["losses"],
                totals["timeouts"],
                template_params["target_pts"],
                template_params["stop_pts"]
            )
            
            results.append({
                "grouping": grouping,
                "totals": totals,
                "kpis": kpis
            })
        
        logger.info(f"Scenario {scenario.id} completed with {len(results)} result rows")
        return results
        
    except Exception as e:
        logger.error(f"Error executing scenario {scenario.id}: {e}")
        raise


async def _execute_single_scenario(
    scenario_id: UUID,
    grouping_types: List[str],
    run_id: UUID
) -> tuple[UUID, bool, Optional[str]]:
    """
    Execute a single scenario with its own database session.
    This allows parallel execution of multiple scenarios.
    
    Args:
        scenario_id: Scenario ID to execute
        grouping_types: List of grouping types to execute
        run_id: Run ID for progress tracking
        
    Returns:
        Tuple of (scenario_id, success, error_message)
    """
    async with AsyncSessionLocal() as scenario_session:
        try:
            # Fetch scenario
            stmt = select(BacktestScenario).where(BacktestScenario.id == scenario_id)
            result = await scenario_session.execute(stmt)
            scenario = result.scalar_one_or_none()
            
            if not scenario:
                return (scenario_id, False, "Scenario not found")
            
            # Update scenario status
            scenario.status = "running"
            await scenario_session.commit()
            
            # Execute for each grouping type
            all_results = []
            for grouping_type in grouping_types:
                try:
                    results = await run_backtest_scenario(scenario_session, scenario, grouping_type)
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"Scenario {scenario.id} grouping {grouping_type} failed: {e}", exc_info=True)
                    await scenario_session.rollback()
                    raise
            
            # Save results
            if all_results:
                await save_results(scenario_session, scenario.id, all_results)
            
            # Mark scenario as completed
            scenario.status = "completed"
            await scenario_session.commit()
            
            logger.info(f"Completed scenario {scenario.id}")
            return (scenario_id, True, None)
            
        except Exception as e:
            error_msg = str(e)[:500]
            logger.error(f"Scenario {scenario_id} failed: {e}", exc_info=True)
            
            # Update scenario status to failed
            try:
                await scenario_session.rollback()
                stmt = select(BacktestScenario).where(BacktestScenario.id == scenario_id)
                result = await scenario_session.execute(stmt)
                failed_scenario = result.scalar_one_or_none()
                if failed_scenario:
                    failed_scenario.status = "failed"
                    failed_scenario.error = error_msg
                    await scenario_session.commit()
            except Exception as update_error:
                logger.error(f"Failed to update scenario {scenario_id} status: {update_error}")
            
            return (scenario_id, False, error_msg)


async def run_backtest_run(
    session: AsyncSession,
    run_id: UUID,
    grouping_types: List[str] = None,
    max_parallel: int = 5
) -> None:
    """
    Execute all scenarios for a backtest run with parallel execution.
    
    Args:
        session: Database session
        run_id: Run ID
        grouping_types: List of grouping types to execute (default: ["hierarchical"])
        max_parallel: Maximum number of scenarios to run in parallel (default: 5)
    """
    if grouping_types is None:
        grouping_types = ["hierarchical"]
    
    # Get run
    from sqlalchemy import select
    stmt = select(BacktestRun).where(BacktestRun.id == run_id)
    result = await session.execute(stmt)
    run = result.scalar_one_or_none()
    
    if not run:
        raise ValueError(f"Run {run_id} not found")
    
    # Update run status
    run.status = "running"
    run.started_at = text("NOW()")
    await session.commit()
    
    logger.info(f"Starting backtest run {run_id} (strategy_type={run.strategy_type}) with {run.total_scenarios} scenarios (max {max_parallel} parallel)")
    
    # Get all scenarios
    stmt = select(BacktestScenario).where(BacktestScenario.run_id == run_id)
    result = await session.execute(stmt)
    scenarios = list(result.scalars().all())
    
    # Log scenario details
    for scenario in scenarios:
        logger.info(f"Found scenario {scenario.id} for run {run_id}: strategy_type={scenario.strategy_type}, params={scenario.params}")
    
    if not scenarios:
        logger.warning(f"No scenarios found for run {run_id}")
        run.status = "failed"
        await session.commit()
        return
    
    # Execute scenarios in parallel batches
    completed = 0
    failed = 0
    
    # Process scenarios in batches to control parallelism
    for i in range(0, len(scenarios), max_parallel):
        batch = scenarios[i:i + max_parallel]
        logger.info(f"Processing batch {i // max_parallel + 1}: {len(batch)} scenarios")
        
        # Execute batch in parallel
        tasks = [
            _execute_single_scenario(scenario.id, grouping_types, run_id)
            for scenario in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and update progress
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Unexpected error in scenario execution: {result}", exc_info=True)
                failed += 1
            else:
                scenario_id, success, error_msg = result
                if success:
                    completed += 1
                else:
                    failed += 1
                
                # Update run progress
                async with AsyncSessionLocal() as progress_session:
                    stmt = select(BacktestRun).where(BacktestRun.id == run_id)
                    result_obj = await progress_session.execute(stmt)
                    run_progress = result_obj.scalar_one_or_none()
                    if run_progress:
                        run_progress.completed_scenarios = completed
                        await progress_session.commit()
        
        logger.info(f"Batch completed: {completed} succeeded, {failed} failed out of {completed + failed}/{run.total_scenarios}")
    
    # Final status update
    run.status = "completed" if failed == 0 and completed == run.total_scenarios else "failed"
    run.completed_scenarios = completed
    run.finished_at = text("NOW()")
    await session.commit()
    
    logger.info(f"Backtest run {run_id} completed: {completed} succeeded, {failed} failed out of {run.total_scenarios} scenarios")

