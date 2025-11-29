"""Scenario generation (grid + AI)."""
from typing import List, Dict, Any, Optional
from itertools import product
from app.models.backtest import ScenarioParams
from app.services.ai import ai_service
from app.core.logging import logger


def generate_grid_scenarios(
    entry_time_starts: List[str],
    entry_time_ends: List[str],
    trade_end_times: List[str],
    target_pts_list: List[float],
    stop_pts_list: List[float],
    directions: List[Optional[str]],
    year_start: int,
    year_end: int,
    # Trend filter parameters
    trend_enabled: bool = False,
    trend_timeframe: str = "15m",
    trend_period: int = 20,
    trend_type: str = "sma",
    trend_strict: bool = True
) -> List[ScenarioParams]:
    """
    Generate all possible combinations of scenario parameters (grid search).
    
    Args:
        entry_time_starts: List of entry window start times (HH:MM:SS)
        entry_time_ends: List of entry window end times (HH:MM:SS)
        trade_end_times: List of trade end times (HH:MM:SS)
        target_pts_list: List of target point values
        stop_pts_list: List of stop loss point values
        directions: List of directions (None, "bullish", "bearish")
        year_start: Start year
        year_end: End year
        trend_enabled: Enable trend filtering
        trend_timeframe: Timeframe for trend calculation (e.g., '15m', '30m', '1h')
        trend_period: Period for moving average
        trend_type: Type of moving average ('sma' or 'ema')
        trend_strict: If True, only trade in trend direction
        
    Returns:
        List of all scenario combinations
    """
    scenarios = []
    
    # Generate entry time pairs
    # If lists have same length and are identical, pair by index (discrete entry points)
    # Otherwise, generate all combinations (entry windows)
    if len(entry_time_starts) == len(entry_time_ends) and entry_time_starts == entry_time_ends:
        # Pair by index: each entry time is a discrete point (start = end)
        entry_time_pairs = list(zip(entry_time_starts, entry_time_ends))
    else:
        # Generate all combinations: entry windows
        entry_time_pairs = list(product(entry_time_starts, entry_time_ends))
    
    # Generate TP/SL pairs
    # If lists have same length, generate matching pairs by index (for RR factor)
    # Otherwise, generate all combinations
    if len(target_pts_list) == len(stop_pts_list):
        # Generate matching pairs by index (RR factor enforced)
        tp_sl_pairs = list(zip(target_pts_list, stop_pts_list))
    else:
        # Generate all combinations
        tp_sl_pairs = list(product(target_pts_list, stop_pts_list))
    
    # Generate all combinations using itertools.product
    for combo in product(
        entry_time_pairs,
        trade_end_times,
        tp_sl_pairs,
        directions
    ):
        (entry_start, entry_end), trade_end, (target_pts, stop_pts), direction = combo
        
        # Validate: entry_end must be >= entry_start
        if entry_end < entry_start:
            continue
        
        # Validate: trade_end should be >= entry_end (reasonable constraint)
        if trade_end < entry_end:
            continue
        
        try:
            scenario = ScenarioParams(
                entry_time_start=entry_start,
                entry_time_end=entry_end,
                trade_end_time=trade_end,
                target_pts=target_pts,
                stop_pts=stop_pts,
                direction=direction,
                year_start=year_start,
                year_end=year_end,
                # Add trend params if enabled
                trend_enabled=trend_enabled if trend_enabled else None,
                trend_timeframe=trend_timeframe if trend_enabled else None,
                trend_period=trend_period if trend_enabled else None,
                trend_type=trend_type if trend_enabled else None,
                trend_strict=trend_strict if trend_enabled else None,
            )
            scenarios.append(scenario)
        except Exception as e:
            logger.warning(f"Skipping invalid scenario combination: {e}")
            continue
    
    # Calculate total combinations
    if len(entry_time_starts) == len(entry_time_ends) and entry_time_starts == entry_time_ends:
        # Discrete entry points (paired by index)
        entry_time_combinations = len(entry_time_starts)
    else:
        # Entry windows (all combinations)
        entry_time_combinations = len(entry_time_starts) * len(entry_time_ends)
    
    if len(target_pts_list) == len(stop_pts_list):
        # Matching pairs by index
        tp_sl_combinations = len(target_pts_list)
    else:
        # All combinations
        tp_sl_combinations = len(target_pts_list) * len(stop_pts_list)
    
    total_combinations = entry_time_combinations * len(trade_end_times) * tp_sl_combinations * len(directions)
    logger.info(f"Generated {len(scenarios)} grid scenarios from {total_combinations} possible combinations")
    return scenarios


async def generate_ai_scenarios(
    recent_results: List[dict] = None,
    context: str = None
) -> List[ScenarioParams]:
    """
    Generate scenarios using AI.
    
    Args:
        recent_results: Recent backtest results for context
        context: Additional context string
        
    Returns:
        List of AI-generated scenarios
    """
    scenarios = await ai_service.suggest_scenarios(recent_results, context)
    logger.info(f"Generated {len(scenarios)} AI scenarios")
    return scenarios

