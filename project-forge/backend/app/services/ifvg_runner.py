"""iFVG Reversal strategy runner."""
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.models.orm import BacktestScenario
from app.services.sql_templates import template_engine
from app.services.fvg_detector import (
    detect_fvgs,
    detect_inversions,
    compute_rr,
    get_timeframe_minutes,
    detect_swing_highs_lows,
    is_fvg_at_liquidity_level
)
from app.services.tz import parse_time_string
from app.core.logging import logger


async def generate_ifvg_trades_only(
    session: AsyncSession,
    scenario: BacktestScenario,
    filter_year: Optional[int] = None,
    filter_month: Optional[int] = None,
    filter_day_of_week: Optional[int] = None,
    filter_direction: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate trades for an iFVG scenario without aggregating results.
    This is used for exporting trades with full FVG/inversion details.
    
    Args:
        session: Database session
        scenario: Scenario to execute
        filter_year: Optional year filter to narrow date range
        filter_month: Optional month filter (1-12)
        filter_day_of_week: Optional day of week filter (0=Monday, 6=Sunday)
        filter_direction: Optional direction filter ('bullish' or 'bearish')
    
    Returns:
        List of trade dictionaries with all FVG/inversion details
    """
    # Reuse the main runner logic but stop before aggregation
    # We'll extract just the trades generation part
    params = scenario.params
    
    # Extract parameters
    fvg_timeframe = params.get('fvg_timeframe', '5m')
    entry_timeframe = params.get('entry_timeframe', '1m')
    wait_candles = int(params.get('wait_candles', 3))
    use_adaptive_rr = params.get('use_adaptive_rr', True)
    cutoff_time = params.get('cutoff_time', '16:00:00')
    
    # Date range - narrow if filters provided
    year_start = params.get('year_start')
    year_end = params.get('year_end')
    date_start = params.get('date_start')
    date_end = params.get('date_end')
    
    # Apply filters to narrow date range for performance
    if filter_year is not None:
        # Narrow to specific year
        if year_start is not None:
            year_start = max(year_start, filter_year)
        else:
            year_start = filter_year
        if year_end is not None:
            year_end = min(year_end, filter_year)
        else:
            year_end = filter_year
        if filter_month is not None:
            # Narrow to specific month
            from datetime import date
            if date_start is None:
                date_start = date(filter_year, filter_month, 1).isoformat()
            if date_end is None:
                # Last day of month
                if filter_month == 12:
                    next_month = date(filter_year + 1, 1, 1)
                else:
                    next_month = date(filter_year, filter_month + 1, 1)
                from datetime import timedelta
                date_end = (next_month - timedelta(days=1)).isoformat()
    
    # Time filter - convert to datetime.time objects
    from datetime import time as dt_time
    time_start_str = params.get('time_start')
    time_end_str = params.get('time_end')
    if time_start_str:
        time_str = parse_time_string(time_start_str)
        time_parts = time_str.split(":")
        time_start = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
    else:
        time_start = None
    if time_end_str:
        time_str = parse_time_string(time_end_str)
        time_parts = time_str.split(":")
        time_end = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
    else:
        time_end = None
    
    # Liquidity filter
    liquidity_enabled = params.get('liquidity_enabled', False)
    liquidity_timeframe = params.get('liquidity_timeframe')
    swing_lookback = int(params.get('swing_lookback', 5)) if liquidity_enabled else None
    tolerance_pts = float(params.get('tolerance_pts', 10.0)) if liquidity_enabled else None
    
    # Fetch candle data (same as main runner)
    from app.services.sql_templates import template_engine
    from sqlalchemy import text
    
    data_sql_params = {
        "fvg_timeframe": fvg_timeframe,
        "entry_timeframe": entry_timeframe
    }
    
    if date_start and date_end:
        data_sql_params["date_start"] = date_start
        data_sql_params["date_end"] = date_end
    else:
        data_sql_params["year_start"] = int(year_start)
        data_sql_params["year_end"] = int(year_end)
    
    if liquidity_enabled and liquidity_timeframe:
        data_sql_params["liquidity_timeframe"] = liquidity_timeframe
    
    data_sql = template_engine.render_ifvg_data(data_sql_params)
    result = await session.execute(text(data_sql))
    rows = result.fetchall()
    
    if len(rows) == 0:
        return []
    
    # Convert to pandas DataFrame
    import pandas as pd
    df = pd.DataFrame([
        {
            'ts_ny': row.ts_ny,
            'timeframe': row.timeframe,
            'open_price': float(row.open_price),
            'high_price': float(row.high_price),
            'low_price': float(row.low_price),
            'close_price': float(row.close_price)
        }
        for row in rows
    ])
    
    # Detect FVGs
    fvg_df = df[df['timeframe'] == fvg_timeframe].copy()
    if len(fvg_df) < 3:
        return []
    
    from app.services.fvg_detector import detect_fvgs, detect_inversions
    fvgs = detect_fvgs(fvg_df, fvg_timeframe)
    
    if len(fvgs) == 0:
        return []
    
    # Apply liquidity filter if enabled
    if liquidity_enabled and liquidity_timeframe:
        liquidity_df = df[df['timeframe'] == liquidity_timeframe].copy()
        if len(liquidity_df) >= (swing_lookback * 2 + 1):
            from app.services.fvg_detector import detect_swing_highs_lows, is_fvg_at_liquidity_level
            swing_points = detect_swing_highs_lows(liquidity_df, liquidity_timeframe, swing_lookback)
            if len(swing_points) > 0:
                fvgs = [fvg for fvg in fvgs if is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts)]
                if len(fvgs) == 0:
                    return []
    
    # Detect inversions
    from app.services.fvg_detector import get_timeframe_minutes
    inversions = detect_inversions(
        fvgs,
        fvg_df,
        wait_candles,
        get_timeframe_minutes(fvg_timeframe)
    )
    
    if len(inversions) == 0:
        return []
    
    # Filter inversions by direction early if filter provided (performance optimization)
    if filter_direction is not None and filter_direction != '' and filter_direction != 'auto' and filter_direction != '-':
        filter_dir_lower = filter_direction.lower().strip()
        # inv_dir is the trade direction (opposite of fvg_direction)
        # For bullish trades, we want inv_dir == 'bullish'
        # For bearish trades, we want inv_dir == 'bearish'
        inversions = [inv for inv in inversions if inv.get('inv_dir', '').lower() == filter_dir_lower]
        if len(inversions) == 0:
            return []
    
    # Generate trades (same logic as main runner)
    trades = []
    entry_df = df[df['timeframe'] == entry_timeframe].copy().sort_values('ts_ny')
    
    for inv in inversions:
        inv_ts = inv['inv_ts']
        inv_dir = inv['inv_dir']
        fvg_ts = inv['fvg_ts']
        fvg_direction = inv.get('fvg_direction', 'bullish' if inv_dir == 'bearish' else 'bearish')
        gap_low = inv['gap_low']
        gap_high = inv['gap_high']
        fvg_size = inv['fvg_size']
        inv_open_price = inv.get('inv_open_price')
        inv_close_price = inv.get('inv_close_price')
        
        entry_candles = entry_df[entry_df['ts_ny'] > inv_ts]
        if len(entry_candles) == 0:
            continue
        
        entry_candle = entry_candles.iloc[0]
        entry_price = entry_candle['open_price']
        entry_ts = entry_candle['ts_ny']
        trading_date = entry_ts.date()
        entry_time = entry_ts.time()
        
        # Apply time filter
        if time_start is not None and entry_time < time_start:
            continue
        if time_end is not None and entry_time > time_end:
            continue
        
        # Apply day of week filter if provided
        if filter_day_of_week is not None:
            if trading_date.weekday() != filter_day_of_week:
                continue
        
        # Compute TP/SL
        from app.services.fvg_detector import compute_rr
        rr_params = {
            'use_adaptive_rr': use_adaptive_rr,
            'target_pts': params.get('target_pts'),
            'stop_pts': params.get('stop_pts'),
            'extra_margin_pts': float(params.get('extra_margin_pts', 5.0)),
            'rr_multiple': float(params.get('rr_multiple', 2.0))
        }
        
        stop_loss, take_profit = compute_rr(entry_price, gap_low, gap_high, inv_dir, rr_params)
        
        # Simulate trade path
        path_sql = template_engine.render_ifvg_path({
            "entry_ts_ny": entry_ts.isoformat(),
            "cutoff_time": cutoff_time,
            "trading_date": trading_date.isoformat()
        })
        
        path_result = await session.execute(text(path_sql))
        path_rows = path_result.fetchall()
        
        if len(path_rows) == 0:
            trades.append({
                'trading_date': trading_date,
                'direction': inv_dir,
                'entry_price': entry_price,
                'entry_ts': entry_ts,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'fvg_size': fvg_size,
                'fvg_ts': fvg_ts,
                'inv_ts': inv_ts,
                'gap_low': gap_low,
                'gap_high': gap_high,
                'fvg_direction': fvg_direction,
                'inv_open_price': inv_open_price,
                'inv_close_price': inv_close_price,
                'use_adaptive_rr': use_adaptive_rr,
                'outcome': 'timeout',
                'exit_price': None,
                'exit_ts': None
            })
            continue
        
        # Check for TP/SL hit
        outcome = 'timeout'
        exit_price = None
        exit_ts = None
        
        for path_row in path_rows:
            high = float(path_row.high_price)
            low = float(path_row.low_price)
            ts = path_row.ts_ny
            
            if inv_dir == 'bullish':
                if high >= take_profit:
                    outcome = 'win'
                    exit_price = take_profit
                    exit_ts = ts
                    break
                if low <= stop_loss:
                    outcome = 'loss'
                    exit_price = stop_loss
                    exit_ts = ts
                    break
            else:  # bearish
                if low <= take_profit:
                    outcome = 'win'
                    exit_price = take_profit
                    exit_ts = ts
                    break
                if high >= stop_loss:
                    outcome = 'loss'
                    exit_price = stop_loss
                    exit_ts = ts
                    break
        
        trades.append({
            'trading_date': trading_date,
            'direction': inv_dir,
            'entry_price': entry_price,
            'entry_ts': entry_ts,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'fvg_size': fvg_size,
            'fvg_ts': fvg_ts,
            'inv_ts': inv_ts,
            'gap_low': gap_low,
            'gap_high': gap_high,
            'fvg_direction': fvg_direction,
            'inv_open_price': inv_open_price,
            'inv_close_price': inv_close_price,
            'use_adaptive_rr': use_adaptive_rr,
            'outcome': outcome,
            'exit_price': exit_price,
            'exit_ts': exit_ts
        })
    
    return trades


async def run_ifvg_scenario(
    session: AsyncSession,
    scenario: BacktestScenario,
    grouping_type: str = "hierarchical"
) -> List[Dict[str, Any]]:
    """
    Execute an iFVG backtest scenario.
    
    Args:
        session: Database session
        scenario: Scenario to execute
        grouping_type: Type of grouping (currently only "hierarchical" supported)
        
    Returns:
        List of result dictionaries
    """
    params = scenario.params
    
    # Extract parameters
    fvg_timeframe = params.get("fvg_timeframe", "5m")
    entry_timeframe = params.get("entry_timeframe", "1m")
    wait_candles = int(params.get("wait_candles", 24))
    use_adaptive_rr = params.get("use_adaptive_rr", True)
    cutoff_time = parse_time_string(params.get("cutoff_time", "16:00:00"))
    
    # Date range parameters (date_start/date_end take precedence over year_start/year_end)
    date_start = params.get("date_start")
    date_end = params.get("date_end")
    year_start = params.get("year_start")
    year_end = params.get("year_end")
    
    # Validate: need either date range or year range
    if not date_start and not year_start:
        logger.error(f"Either date_start or year_start must be provided for scenario {scenario.id}")
        return []
    if not date_end and not year_end:
        logger.error(f"Either date_end or year_end must be provided for scenario {scenario.id}")
        return []
    
    # Time filter parameters (optional)
    time_start_str = params.get("time_start")
    time_end_str = params.get("time_end")
    # Parse time strings to datetime.time objects for comparison
    from datetime import time as dt_time
    if time_start_str:
        time_str = parse_time_string(time_start_str)
        time_parts = time_str.split(":")
        time_start = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
    else:
        time_start = None
    if time_end_str:
        time_str = parse_time_string(time_end_str)
        time_parts = time_str.split(":")
        time_end = dt_time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0)
    else:
        time_end = None
    
    # Liquidity filter parameters
    liquidity_enabled = params.get("liquidity_enabled", False)
    liquidity_timeframe = params.get("liquidity_timeframe")
    swing_lookback = int(params.get("swing_lookback", 5))
    tolerance_pts = float(params.get("tolerance_pts", 5.0))
    
    date_range_str = f"{date_start} to {date_end}" if date_start else f"{year_start}-{year_end}"
    time_filter_str = f"{time_start_str} to {time_end_str}" if time_start_str else "all day"
    logger.info(f"Running iFVG scenario {scenario.id}: {fvg_timeframe} FVG, {entry_timeframe} entry, wait={wait_candles}, date={date_range_str}, time={time_filter_str}, liquidity_filter={'enabled' if liquidity_enabled else 'disabled'}")
    
    # Step 1: Fetch candle data via SQL
    data_sql_params = {
        "fvg_timeframe": fvg_timeframe,
        "entry_timeframe": entry_timeframe,
    }
    
    # Add date range (date_start/date_end takes precedence)
    if date_start and date_end:
        data_sql_params["date_start"] = date_start
        data_sql_params["date_end"] = date_end
    elif year_start and year_end:
        data_sql_params["year_start"] = int(year_start)
        data_sql_params["year_end"] = int(year_end)
    
    if liquidity_enabled and liquidity_timeframe:
        data_sql_params["liquidity_timeframe"] = liquidity_timeframe
    
    data_sql = template_engine.render_ifvg_data(data_sql_params)
    
    date_range_desc = f"{date_start} to {date_end}" if date_start else f"years {year_start}-{year_end}"
    logger.info(f"Fetching candle data for iFVG scenario {scenario.id}: {fvg_timeframe} FVG, {entry_timeframe} entry, {date_range_desc}")
    result = await session.execute(text(data_sql))
    rows = result.fetchall()
    
    logger.info(f"Fetched {len(rows)} rows from database for scenario {scenario.id}")
    
    if len(rows) == 0:
        logger.warning(f"No candle data found for scenario {scenario.id} - check if data exists for timeframes {fvg_timeframe} and {entry_timeframe} for years {year_start}-{year_end}")
        return []
    
    # Convert to pandas DataFrame
    try:
        df = pd.DataFrame([
            {
                'ts_ny': row.ts_ny,
                'timeframe': row.timeframe,
                'open_price': float(row.open_price),
                'high_price': float(row.high_price),
                'low_price': float(row.low_price),
                'close_price': float(row.close_price)
            }
            for row in rows
        ])
        logger.info(f"Created DataFrame with {len(df)} rows, timeframes: {df['timeframe'].unique().tolist()}")
    except Exception as e:
        logger.error(f"Error converting rows to DataFrame for scenario {scenario.id}: {e}")
        return []
    
    # Step 2: Detect FVGs on FVG timeframe
    fvg_df = df[df['timeframe'] == fvg_timeframe].copy()
    logger.info(f"Filtered to {len(fvg_df)} {fvg_timeframe} candles for FVG detection")
    
    if len(fvg_df) < 3:
        logger.warning(f"Insufficient {fvg_timeframe} candles ({len(fvg_df)}) for FVG detection - need at least 3")
        return []
    
    fvgs = detect_fvgs(fvg_df, fvg_timeframe)
    logger.info(f"Detected {len(fvgs)} FVGs for scenario {scenario.id}")
    
    if len(fvgs) == 0:
        logger.info(f"No FVGs detected for scenario {scenario.id} - this may be normal if market conditions don't create gaps")
        return []
    
    # Step 2.5: Apply liquidity filter if enabled
    if liquidity_enabled and liquidity_timeframe:
        logger.info(f"Applying liquidity filter: timeframe={liquidity_timeframe}, lookback={swing_lookback}, tolerance={tolerance_pts} pts")
        
        # Get liquidity timeframe data
        liquidity_df = df[df['timeframe'] == liquidity_timeframe].copy()
        
        if len(liquidity_df) < (swing_lookback * 2 + 1):
            logger.warning(f"Insufficient {liquidity_timeframe} candles ({len(liquidity_df)}) for swing detection - need at least {swing_lookback * 2 + 1}")
            logger.info("Proceeding without liquidity filter")
        else:
            # Detect swing highs/lows
            swing_points = detect_swing_highs_lows(liquidity_df, liquidity_timeframe, swing_lookback)
            logger.info(f"Detected {len(swing_points)} swing points on {liquidity_timeframe} timeframe")
            
            if len(swing_points) == 0:
                logger.warning(f"No swing points detected on {liquidity_timeframe} timeframe - proceeding without liquidity filter")
            else:
                # Filter FVGs to only those at liquidity levels
                filtered_fvgs = [
                    fvg for fvg in fvgs
                    if is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts)
                ]
                
                logger.info(f"Liquidity filter: {len(fvgs)} FVGs -> {len(filtered_fvgs)} FVGs at liquidity levels")
                fvgs = filtered_fvgs
                
                if len(fvgs) == 0:
                    logger.info(f"No FVGs at liquidity levels for scenario {scenario.id} - no trades will be generated")
                    return []
    
    # Step 3: Detect inversions
    # Use FVG timeframe candles for inversion detection (as per spec)
    inversions = detect_inversions(
        fvgs,
        fvg_df,
        wait_candles,
        get_timeframe_minutes(fvg_timeframe)
    )
    logger.info(f"Detected {len(inversions)} inversions from {len(fvgs)} FVGs for scenario {scenario.id}")
    
    if len(inversions) == 0:
        logger.info(f"No inversions detected for scenario {scenario.id} - FVGs were not closed by opposing candles within {wait_candles} candles")
        return []
    
    # Step 4: Process each inversion to create trades
    trades = []
    entry_df = df[df['timeframe'] == entry_timeframe].copy().sort_values('ts_ny')
    
    for inv in inversions:
        inv_ts = inv['inv_ts']
        inv_dir = inv['inv_dir']
        fvg_ts = inv['fvg_ts']
        fvg_direction = inv.get('fvg_direction', 'bullish' if inv_dir == 'bearish' else 'bearish')  # Fallback if not in inversion dict
        gap_low = inv['gap_low']
        gap_high = inv['gap_high']
        fvg_size = inv['fvg_size']
        inv_open_price = inv.get('inv_open_price')
        inv_close_price = inv.get('inv_close_price')
        
        # Get entry price from next candle on entry_timeframe after inversion
        entry_candles = entry_df[entry_df['ts_ny'] > inv_ts]
        if len(entry_candles) == 0:
            continue
        
        entry_candle = entry_candles.iloc[0]
        entry_price = entry_candle['open_price']
        entry_ts = entry_candle['ts_ny']
        trading_date = entry_ts.date()
        entry_time = entry_ts.time()
        
        # Apply time filter if specified
        if time_start is not None or time_end is not None:
            # Check if entry time is within time filter range
            if time_start is not None and entry_time < time_start:
                continue  # Skip this trade - before time_start
            if time_end is not None and entry_time > time_end:
                continue  # Skip this trade - after time_end
        
        # Compute TP/SL
        rr_params = {
            'use_adaptive_rr': use_adaptive_rr,
            'target_pts': params.get('target_pts'),
            'stop_pts': params.get('stop_pts'),
            'extra_margin_pts': float(params.get('extra_margin_pts', 5.0)),
            'rr_multiple': float(params.get('rr_multiple', 2.0))
        }
        
        stop_loss, take_profit = compute_rr(entry_price, gap_low, gap_high, inv_dir, rr_params)
        
        # Step 5: Simulate trade path
        path_sql = template_engine.render_ifvg_path({
            "entry_ts_ny": entry_ts.isoformat(),
            "cutoff_time": cutoff_time,
            "trading_date": trading_date.isoformat()
        })
        
        path_result = await session.execute(text(path_sql))
        path_rows = path_result.fetchall()
        
        if len(path_rows) == 0:
            # No path data - mark as timeout
            trades.append({
                'trading_date': trading_date,
                'direction': inv_dir,
                'entry_price': entry_price,
                'entry_ts': entry_ts,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'fvg_size': fvg_size,
                'fvg_ts': fvg_ts,
                'inv_ts': inv_ts,
                'gap_low': gap_low,
                'gap_high': gap_high,
                'fvg_direction': fvg_direction,
                'inv_open_price': inv_open_price,
                'inv_close_price': inv_close_price,
                'use_adaptive_rr': use_adaptive_rr,
                'outcome': 'timeout',
                'exit_price': None,
                'exit_ts': None
            })
            continue
        
        # Check for TP/SL hit
        outcome = 'timeout'
        exit_price = None
        exit_ts = None
        
        for path_row in path_rows:
            high = float(path_row.high_price)
            low = float(path_row.low_price)
            ts = path_row.ts_ny
            
            if inv_dir == 'bullish':
                # Check TP first (higher priority)
                if high >= take_profit:
                    outcome = 'win'
                    exit_price = take_profit
                    exit_ts = ts
                    break
                # Check SL
                if low <= stop_loss:
                    outcome = 'loss'
                    exit_price = stop_loss
                    exit_ts = ts
                    break
            else:  # bearish
                # Check TP first
                if low <= take_profit:
                    outcome = 'win'
                    exit_price = take_profit
                    exit_ts = ts
                    break
                # Check SL
                if high >= stop_loss:
                    outcome = 'loss'
                    exit_price = stop_loss
                    exit_ts = ts
                    break
        
        trades.append({
            'trading_date': trading_date,
            'direction': inv_dir,
            'entry_price': entry_price,
            'entry_ts': entry_ts,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'fvg_size': fvg_size,
            'fvg_ts': fvg_ts,
            'inv_ts': inv_ts,
            'gap_low': gap_low,
            'gap_high': gap_high,
            'fvg_direction': fvg_direction,
            'inv_open_price': inv_open_price,
            'inv_close_price': inv_close_price,
            'use_adaptive_rr': use_adaptive_rr,
            'outcome': outcome,
            'exit_price': exit_price,
            'exit_ts': exit_ts
        })
    
    logger.info(f"Processed {len(trades)} trades from {len(inversions)} inversions for scenario {scenario.id}")
    
    # Step 6: Aggregate results by year, direction, RR mode
    if len(trades) == 0:
        logger.warning(f"No trades generated from {len(inversions)} inversions for scenario {scenario.id} - check entry timeframe data availability")
        return []
    
    trades_df = pd.DataFrame(trades)
    trades_df['year'] = trades_df['trading_date'].apply(lambda x: x.year)
    trades_df['month'] = trades_df['trading_date'].apply(lambda x: x.month)
    # Add day of week (0=Monday, 6=Sunday in pandas, but we'll use ISO: Monday=0, Sunday=6)
    # Python datetime.weekday(): Monday=0, Sunday=6
    trades_df['day_of_week'] = trades_df['trading_date'].apply(lambda x: x.weekday())
    
    # Determine grouping strategy based on date/time filters
    date_range_days = None
    if date_start and date_end:
        from datetime import datetime as dt
        start_dt = dt.strptime(date_start, '%Y-%m-%d')
        end_dt = dt.strptime(date_end, '%Y-%m-%d')
        date_range_days = (end_dt - start_dt).days + 1
    
    has_time_filter = time_start is not None or time_end is not None
    
    logger.info(f"Creating result aggregations for scenario {scenario.id}: {len(trades_df)} trades, date_range={date_range_days} days, time_filter={has_time_filter}")
    
    # Group by year, direction, and RR mode (with smart grouping)
    results = []
    
    # Overall strategy level
    strategy_totals = {
        'total_trades': len(trades_df),
        'wins': len(trades_df[trades_df['outcome'] == 'win']),
        'losses': len(trades_df[trades_df['outcome'] == 'loss']),
        'timeouts': len(trades_df[trades_df['outcome'] == 'timeout'])
    }
    
    strategy_kpis = _calculate_ifvg_kpis(trades_df, use_adaptive_rr)
    
    logger.info(f"Strategy-level totals: {strategy_totals}, KPIs: {strategy_kpis}")
    
    results.append({
        'grouping': {
            'level': 'strategy',
            'grouping_type': grouping_type,
            'fvg_timeframe': fvg_timeframe,
            'entry_timeframe': entry_timeframe,
            'use_adaptive_rr': use_adaptive_rr
        },
        'totals': strategy_totals,
        'kpis': strategy_kpis
    })
    
    # Smart grouping: if date range is narrow (< 30 days), skip year grouping
    group_by_year = date_range_days is None or date_range_days >= 30
    
    if group_by_year:
        # By year
        for year in sorted(trades_df['year'].unique()):
            year_trades = trades_df[trades_df['year'] == year]
            year_totals = {
                'total_trades': len(year_trades),
                'wins': len(year_trades[year_trades['outcome'] == 'win']),
                'losses': len(year_trades[year_trades['outcome'] == 'loss']),
                'timeouts': len(year_trades[year_trades['outcome'] == 'timeout'])
            }
            year_kpis = _calculate_ifvg_kpis(year_trades, use_adaptive_rr)
            
            results.append({
                'grouping': {
                    'level': 'year',
                    'grouping_type': grouping_type,
                    'year': int(year),
                    'fvg_timeframe': fvg_timeframe,
                    'entry_timeframe': entry_timeframe,
                    'use_adaptive_rr': use_adaptive_rr
                },
                'totals': year_totals,
                'kpis': year_kpis
            })
            
            # By day of week within year (for day of week grouping)
            for dow in sorted(trades_df['day_of_week'].unique()):
                dow_trades = year_trades[year_trades['day_of_week'] == dow]
                if len(dow_trades) == 0:
                    continue
                
                dow_totals = {
                    'total_trades': len(dow_trades),
                    'wins': len(dow_trades[dow_trades['outcome'] == 'win']),
                    'losses': len(dow_trades[dow_trades['outcome'] == 'loss']),
                    'timeouts': len(dow_trades[dow_trades['outcome'] == 'timeout'])
                }
                dow_kpis = _calculate_ifvg_kpis(dow_trades, use_adaptive_rr)
                
                results.append({
                    'grouping': {
                        'level': 'year_dow',
                        'grouping_type': grouping_type,
                        'year': int(year),
                        'day_of_week': int(dow),
                        'fvg_timeframe': fvg_timeframe,
                        'entry_timeframe': entry_timeframe,
                        'use_adaptive_rr': use_adaptive_rr
                    },
                    'totals': dow_totals,
                    'kpis': dow_kpis
                })
            
            # By direction within year
            for direction in ['bullish', 'bearish']:
                dir_trades = year_trades[year_trades['direction'] == direction]
                if len(dir_trades) == 0:
                    continue
                
                dir_totals = {
                    'total_trades': len(dir_trades),
                    'wins': len(dir_trades[dir_trades['outcome'] == 'win']),
                    'losses': len(dir_trades[dir_trades['outcome'] == 'loss']),
                    'timeouts': len(dir_trades[dir_trades['outcome'] == 'timeout'])
                }
                dir_kpis = _calculate_ifvg_kpis(dir_trades, use_adaptive_rr)
                
                results.append({
                    'grouping': {
                        'level': 'year_direction',
                        'grouping_type': grouping_type,
                        'year': int(year),
                        'direction': direction,
                        'fvg_timeframe': fvg_timeframe,
                        'entry_timeframe': entry_timeframe,
                        'use_adaptive_rr': use_adaptive_rr
                    },
                    'totals': dir_totals,
                    'kpis': dir_kpis
                })
    else:
        # Narrow date range: group by direction (and month if spans multiple months)
        unique_months = trades_df['month'].unique()
        if len(unique_months) > 1:
            # Group by month
            for year in sorted(trades_df['year'].unique()):
                for month in sorted(trades_df[trades_df['year'] == year]['month'].unique()):
                    month_trades = trades_df[(trades_df['year'] == year) & (trades_df['month'] == month)]
                    if len(month_trades) == 0:
                        continue
                    
                    month_totals = {
                        'total_trades': len(month_trades),
                        'wins': len(month_trades[month_trades['outcome'] == 'win']),
                        'losses': len(month_trades[month_trades['outcome'] == 'loss']),
                        'timeouts': len(month_trades[month_trades['outcome'] == 'timeout'])
                    }
                    month_kpis = _calculate_ifvg_kpis(month_trades, use_adaptive_rr)
                    
                    results.append({
                        'grouping': {
                            'level': 'year_month',
                            'grouping_type': grouping_type,
                            'year': int(year),
                            'month': int(month),
                            'fvg_timeframe': fvg_timeframe,
                            'entry_timeframe': entry_timeframe,
                            'use_adaptive_rr': use_adaptive_rr
                        },
                        'totals': month_totals,
                        'kpis': month_kpis
                    })
        
        # Always group by direction
        for direction in ['bullish', 'bearish']:
            dir_trades = trades_df[trades_df['direction'] == direction]
            if len(dir_trades) == 0:
                continue
            
            dir_totals = {
                'total_trades': len(dir_trades),
                'wins': len(dir_trades[dir_trades['outcome'] == 'win']),
                'losses': len(dir_trades[dir_trades['outcome'] == 'loss']),
                'timeouts': len(dir_trades[dir_trades['outcome'] == 'timeout'])
            }
            dir_kpis = _calculate_ifvg_kpis(dir_trades, use_adaptive_rr)
            
            results.append({
                'grouping': {
                    'level': 'direction',
                    'grouping_type': grouping_type,
                    'direction': direction,
                    'fvg_timeframe': fvg_timeframe,
                    'entry_timeframe': entry_timeframe,
                    'use_adaptive_rr': use_adaptive_rr
                },
                'totals': dir_totals,
                'kpis': dir_kpis
            })
    
    logger.info(f"iFVG scenario {scenario.id} completed with {len(results)} result rows")
    return results


def _calculate_ifvg_kpis(trades_df: pd.DataFrame, use_adaptive_rr: bool) -> Dict[str, Any]:
    """Calculate iFVG-specific KPIs."""
    if len(trades_df) == 0:
        return {
            "win_rate_percent": 0.0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "timeouts": 0,
            "avg_fvg_size": None,
            "avg_tp_pts": None,
            "avg_sl_pts": None,
            "expectancy_r": None,
            "profit_factor": None
        }
    
    total_trades = len(trades_df)
    wins = len(trades_df[trades_df['outcome'] == 'win'])
    losses = len(trades_df[trades_df['outcome'] == 'loss'])
    timeouts = len(trades_df[trades_df['outcome'] == 'timeout'])
    
    win_rate = (wins / total_trades) * 100.0 if total_trades > 0 else 0.0
    
    # FVG-specific metrics
    avg_fvg_size = float(trades_df['fvg_size'].mean()) if 'fvg_size' in trades_df.columns else None
    
    # Calculate average TP/SL in points
    if use_adaptive_rr:
        trades_df['tp_pts'] = abs(trades_df['take_profit'] - trades_df['entry_price'])
        trades_df['sl_pts'] = abs(trades_df['stop_loss'] - trades_df['entry_price'])
    else:
        # For fixed mode, use the actual differences
        trades_df['tp_pts'] = abs(trades_df['take_profit'] - trades_df['entry_price'])
        trades_df['sl_pts'] = abs(trades_df['stop_loss'] - trades_df['entry_price'])
    
    avg_tp_pts = float(trades_df['tp_pts'].mean()) if 'tp_pts' in trades_df.columns else None
    avg_sl_pts = float(trades_df['sl_pts'].mean()) if 'sl_pts' in trades_df.columns else None
    
    # Expectancy in R
    if avg_tp_pts and avg_sl_pts and avg_sl_pts > 0:
        r_ratio = avg_tp_pts / avg_sl_pts
        win_rate_decimal = win_rate / 100.0
        loss_rate_decimal = losses / total_trades if total_trades > 0 else 0
        expectancy_r = (win_rate_decimal * r_ratio) - (loss_rate_decimal * 1.0)
    else:
        expectancy_r = None
    
    # Profit factor
    if losses > 0 and avg_tp_pts and avg_sl_pts:
        profit_factor = (wins * avg_tp_pts) / (losses * avg_sl_pts)
    else:
        profit_factor = None
    
    return {
        "win_rate_percent": round(win_rate, 2),
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "avg_fvg_size": round(avg_fvg_size, 2) if avg_fvg_size is not None else None,
        "avg_tp_pts": round(avg_tp_pts, 2) if avg_tp_pts is not None else None,
        "avg_sl_pts": round(avg_sl_pts, 2) if avg_sl_pts is not None else None,
        "expectancy_r": round(expectancy_r, 4) if expectancy_r is not None else None,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None
    }

