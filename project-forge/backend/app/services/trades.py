"""Service for fetching individual trades."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from typing import Dict, Any, List, Optional
from uuid import UUID
from app.models.orm import BacktestScenario, BacktestResult
from app.services.sql_templates import template_engine
from app.services.tz import parse_time_string
from app.core.logging import logger


async def get_trades_for_result(
    session: AsyncSession,
    result_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get individual trades for a specific result.
    
    Args:
        session: Database session
        result_id: Result ID
        
    Returns:
        List of trade dictionaries
    """
    # Get the result
    stmt = select(BacktestResult).where(BacktestResult.id == result_id)
    result = await session.execute(stmt)
    result_obj = result.scalar_one_or_none()
    
    if not result_obj:
        raise ValueError(f"Result {result_id} not found")
    
    # Get the scenario
    stmt = select(BacktestScenario).where(BacktestScenario.id == result_obj.scenario_id)
    scenario_result = await session.execute(stmt)
    scenario = scenario_result.scalar_one_or_none()
    
    if not scenario:
        raise ValueError(f"Scenario {result_obj.scenario_id} not found")
    
    params = scenario.params
    grouping = result_obj.grouping or {}
    
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
        "trade_end_time": parse_time_string(params.get("trade_end_time", "16:00:00")),
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
    
    # Add filter parameters based on grouping
    if "year" in grouping:
        template_params["filter_year"] = int(grouping["year"])
    if "dow" in grouping:
        template_params["filter_dow"] = int(grouping["dow"])
    if "candle_time" in grouping:
        template_params["filter_candle_time"] = grouping["candle_time"]
    
    # Render and execute SQL
    sql = template_engine.render_trades(template_params)
    
    logger.info(f"Fetching trades for result {result_id}")
    logger.debug(f"SQL query: {sql[:500]}...")
    
    try:
        result = await session.execute(text(sql))
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        trades = []
        for row in rows:
            row_dict = dict(row._mapping)
            trades.append({
                "year": int(row_dict.get("year", 0)),
                "trading_date": str(row_dict.get("trading_date", "")),
                "day_of_week": int(row_dict.get("day_of_week", 0)),
                "day_name": str(row_dict.get("day_name", "")).strip(),
                "entry_time": str(row_dict.get("entry_time", "")),
                "entry_price": float(row_dict.get("entry_price", 0)),
                "target_price": float(row_dict.get("target_price", 0)),
                "stop_price": float(row_dict.get("stop_price", 0)),
                "direction": str(row_dict.get("direction", "")),
                "outcome": str(row_dict.get("outcome", "")),
                "trade_end_time": str(row_dict.get("trade_end_time", "")),
                "exit_time": str(row_dict.get("exit_time", "")),
                # May be NULL if timeout; preserve null instead of converting to 0
                "exit_price": (float(row_dict["exit_price"]) if row_dict.get("exit_price") is not None else None)
            })
        
        logger.info(f"Found {len(trades)} trades for result {result_id}")
        return trades
        
    except Exception as e:
        logger.error(f"Error fetching trades for result {result_id}: {e}")
        raise


