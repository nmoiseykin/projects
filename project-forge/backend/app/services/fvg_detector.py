"""FVG (Fair Value Gap) detection and inversion logic."""
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import timedelta
from app.core.logging import logger


def detect_fvgs(candles_df: pd.DataFrame, timeframe: str) -> List[Dict[str, Any]]:
    """
    Detect Fair Value Gaps (FVGs) in candle data.
    
    FVG Definition:
    - Bullish FVG: low[i] > high[i-2] (gap between candle i-2 and i)
    - Bearish FVG: high[i] < low[i-2] (gap between candle i-2 and i)
    
    Args:
        candles_df: DataFrame with columns: ts_ny, open_price, high_price, low_price, close_price
        timeframe: Timeframe string for logging
        
    Returns:
        List of FVG dictionaries with keys:
        - timestamp: FVG formation timestamp
        - direction: 'bullish' or 'bearish'
        - gap_low: Lower boundary of gap
        - gap_high: Upper boundary of gap
        - fvg_size: Size of gap in points
    """
    fvgs = []
    
    if len(candles_df) < 3:
        logger.debug(f"Insufficient candles for FVG detection: {len(candles_df)}")
        return fvgs
    
    # Sort by timestamp
    df = candles_df.sort_values('ts_ny').reset_index(drop=True)
    
    for i in range(2, len(df)):
        # Bullish FVG: current low > high of 2 candles ago
        if df.loc[i, 'low_price'] > df.loc[i-2, 'high_price']:
            gap_low = df.loc[i-2, 'high_price']
            gap_high = df.loc[i, 'low_price']
            fvg_size = gap_high - gap_low
            
            fvgs.append({
                'timestamp': df.loc[i, 'ts_ny'],
                'direction': 'bullish',
                'gap_low': float(gap_low),
                'gap_high': float(gap_high),
                'fvg_size': float(fvg_size)
            })
        
        # Bearish FVG: current high < low of 2 candles ago
        elif df.loc[i, 'high_price'] < df.loc[i-2, 'low_price']:
            gap_low = df.loc[i, 'high_price']
            gap_high = df.loc[i-2, 'low_price']
            fvg_size = gap_high - gap_low
            
            fvgs.append({
                'timestamp': df.loc[i, 'ts_ny'],
                'direction': 'bearish',
                'gap_low': float(gap_low),
                'gap_high': float(gap_high),
                'fvg_size': float(fvg_size)
            })
    
    logger.info(f"Detected {len(fvgs)} FVGs on {timeframe} timeframe")
    return fvgs


def detect_inversions(
    fvgs: List[Dict[str, Any]],
    candles_df: pd.DataFrame,
    wait_candles: int,
    fvg_timeframe_minutes: int = 5
) -> List[Dict[str, Any]]:
    """
    Detect inversions of FVGs (opposing candles that fully close the gap).
    
    Inversion Conditions:
    - Bullish FVG: close < gap_low AND close < open (bearish candle fully closes gap)
    - Bearish FVG: close > gap_high AND close > open (bullish candle fully closes gap)
    
    Args:
        fvgs: List of FVG dictionaries from detect_fvgs()
        candles_df: DataFrame with all candles (can be different timeframe)
        wait_candles: Number of FVG timeframe candles to wait for inversion
        fvg_timeframe_minutes: Minutes per FVG timeframe candle (default 5 for 5m)
        
    Returns:
        List of inversion dictionaries with keys:
        - fvg_ts: Original FVG timestamp
        - inv_ts: Inversion candle timestamp
        - inv_dir: Direction of inversion ('bullish' or 'bearish')
        - gap_low: FVG gap lower boundary
        - gap_high: FVG gap upper boundary
        - fvg_size: Original FVG size
    """
    inversions = []
    
    if len(candles_df) == 0:
        return inversions
    
    df = candles_df.sort_values('ts_ny').reset_index(drop=True)
    
    for fvg in fvgs:
        fvg_ts = fvg['timestamp']
        gap_low = fvg['gap_low']
        gap_high = fvg['gap_high']
        fvg_dir = fvg['direction']
        
        # Calculate wait window end time
        wait_window_end = fvg_ts + timedelta(minutes=wait_candles * fvg_timeframe_minutes)
        
        # Find candles in the wait window
        window_df = df[(df['ts_ny'] > fvg_ts) & (df['ts_ny'] <= wait_window_end)]
        
        if len(window_df) == 0:
            continue
        
        # Check for inversion based on FVG direction
        if fvg_dir == 'bullish':
            # Bullish FVG inversion: bearish candle that closes below gap_low
            inv_candles = window_df[
                (window_df['close_price'] < gap_low) &
                (window_df['close_price'] < window_df['open_price'])  # Bearish candle
            ]
        else:  # bearish
            # Bearish FVG inversion: bullish candle that closes above gap_high
            inv_candles = window_df[
                (window_df['close_price'] > gap_high) &
                (window_df['close_price'] > window_df['open_price'])  # Bullish candle
            ]
        
        if len(inv_candles) > 0:
            # Take first inversion
            inv_candle = inv_candles.iloc[0]
            inv_dir = 'bearish' if fvg_dir == 'bullish' else 'bullish'
            
            inversions.append({
                'fvg_ts': fvg_ts,
                'inv_ts': inv_candle['ts_ny'],
                'inv_dir': inv_dir,
                'fvg_direction': fvg_dir,  # Original FVG direction
                'gap_low': gap_low,
                'gap_high': gap_high,
                'fvg_size': fvg['fvg_size'],
                'inv_open_price': float(inv_candle['open_price']),  # Inversion candle open price
                'inv_close_price': float(inv_candle['close_price'])  # Inversion candle close price
            })
    
    logger.info(f"Detected {len(inversions)} inversions from {len(fvgs)} FVGs")
    return inversions


def compute_rr(
    entry_price: float,
    fvg_low: float,
    fvg_high: float,
    direction: str,
    params: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Compute Stop Loss and Take Profit prices.
    
    Fixed Mode:
    - Uses target_pts and stop_pts directly
    
    Adaptive Mode:
    - SL = extra_margin_pts beyond FVG opposite boundary
    - TP = (extra_margin_pts + fvg_size) × rr_multiple from entry
    
    Args:
        entry_price: Entry price for the trade
        fvg_low: Lower boundary of FVG gap
        fvg_high: Upper boundary of FVG gap
        direction: Trade direction ('bullish' or 'bearish')
        params: Dictionary with:
            - use_adaptive_rr: bool
            - target_pts: float (if fixed mode)
            - stop_pts: float (if fixed mode)
            - extra_margin_pts: float (if adaptive mode)
            - rr_multiple: float (if adaptive mode)
    
    Returns:
        Tuple of (stop_loss_price, take_profit_price)
    """
    use_adaptive = params.get('use_adaptive_rr', True)
    
    if not use_adaptive:
        # Fixed mode
        target_pts = float(params['target_pts'])
        stop_pts = float(params['stop_pts'])
        
        if direction == 'bullish':
            stop_loss = entry_price - stop_pts
            take_profit = entry_price + target_pts
        else:  # bearish
            stop_loss = entry_price + stop_pts
            take_profit = entry_price - target_pts
    else:
        # Adaptive mode
        fvg_size = fvg_high - fvg_low
        extra_margin = float(params.get('extra_margin_pts', 5.0))
        rr_multiple = float(params.get('rr_multiple', 2.0))
        
        risk_pts = extra_margin + fvg_size
        target_pts = risk_pts * rr_multiple
        
        if direction == 'bullish':
            # SL = gap_low - extra_margin
            stop_loss = fvg_low - extra_margin
            # TP = entry + target_pts
            take_profit = entry_price + target_pts
        else:  # bearish
            # SL = gap_high + extra_margin
            stop_loss = fvg_high + extra_margin
            # TP = entry - target_pts
            take_profit = entry_price - target_pts
    
    return (stop_loss, take_profit)


def get_timeframe_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes."""
    timeframe_map = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440
    }
    return timeframe_map.get(timeframe, 5)


def detect_swing_highs_lows(
    candles_df: pd.DataFrame,
    timeframe: str,
    lookback: int = 5
) -> List[Dict[str, Any]]:
    """
    Detect swing highs and swing lows in candle data.
    
    Swing High: high[i] > max(high[i-lookback:i-1]) AND high[i] > max(high[i+1:i+lookback])
    Swing Low: low[i] < min(low[i-lookback:i-1]) AND low[i] < min(low[i+1:i+lookback])
    
    Args:
        candles_df: DataFrame with columns: ts_ny, high_price, low_price
        timeframe: Timeframe string for logging
        lookback: Number of candles to look back/forward for swing detection
        
    Returns:
        List of swing point dictionaries with keys:
        - timestamp: Swing point timestamp
        - price: Swing high or low price
        - type: 'high' or 'low'
    """
    swings = []
    
    if len(candles_df) < (lookback * 2 + 1):
        logger.debug(f"Insufficient candles for swing detection: {len(candles_df)}, need at least {lookback * 2 + 1}")
        return swings
    
    # Sort by timestamp
    df = candles_df.sort_values('ts_ny').reset_index(drop=True)
    
    for i in range(lookback, len(df) - lookback):
        # Check for swing high
        current_high = df.loc[i, 'high_price']
        left_highs = df.loc[i-lookback:i-1, 'high_price'].max()
        right_highs = df.loc[i+1:i+lookback, 'high_price'].max()
        
        if current_high > left_highs and current_high > right_highs:
            swings.append({
                'timestamp': df.loc[i, 'ts_ny'],
                'price': float(current_high),
                'type': 'high'
            })
        
        # Check for swing low
        current_low = df.loc[i, 'low_price']
        left_lows = df.loc[i-lookback:i-1, 'low_price'].min()
        right_lows = df.loc[i+1:i+lookback, 'low_price'].min()
        
        if current_low < left_lows and current_low < right_lows:
            swings.append({
                'timestamp': df.loc[i, 'ts_ny'],
                'price': float(current_low),
                'type': 'low'
            })
    
    logger.info(f"Detected {len(swings)} swing points ({sum(1 for s in swings if s['type'] == 'high')} highs, {sum(1 for s in swings if s['type'] == 'low')} lows) on {timeframe} timeframe")
    return swings


def is_fvg_at_liquidity_level(
    fvg: Dict[str, Any],
    swing_points: List[Dict[str, Any]],
    tolerance_pts: float
) -> bool:
    """
    Check if an FVG forms at a liquidity level (swing high/low).
    
    For bullish FVG: Check if gap_low is near a swing high (price took out swing high)
    For bearish FVG: Check if gap_high is near a swing low (price took out swing low)
    
    Args:
        fvg: FVG dictionary with keys: direction, gap_low, gap_high, timestamp
        swing_points: List of swing point dictionaries with keys: price, type, timestamp
        tolerance_pts: Price tolerance in points for matching
        
    Returns:
        True if FVG is at a liquidity level, False otherwise
    """
    if not swing_points:
        return False
    
    fvg_dir = fvg['direction']
    fvg_timestamp = fvg['timestamp']
    
    # Find swing points near the FVG timestamp (within reasonable time window)
    # Use a 1-hour window to find relevant swing points
    from datetime import timedelta
    time_window = timedelta(hours=1)
    
    relevant_swings = [
        s for s in swing_points
        if abs((s['timestamp'] - fvg_timestamp).total_seconds()) <= time_window.total_seconds()
    ]
    
    if not relevant_swings:
        return False
    
    if fvg_dir == 'bullish':
        # Bullish FVG: check if gap_low is near a swing high
        # Price gapped up, taking out a swing high
        gap_low = fvg['gap_low']
        for swing in relevant_swings:
            if swing['type'] == 'high':
                price_diff = abs(swing['price'] - gap_low)
                if price_diff <= tolerance_pts:
                    logger.debug(f"Bullish FVG at {fvg_timestamp} matches swing high at {swing['timestamp']} (price diff: {price_diff:.2f} pts)")
                    return True
    else:  # bearish
        # Bearish FVG: check if gap_high is near a swing low
        # Price gapped down, taking out a swing low
        gap_high = fvg['gap_high']
        for swing in relevant_swings:
            if swing['type'] == 'low':
                price_diff = abs(swing['price'] - gap_high)
                if price_diff <= tolerance_pts:
                    logger.debug(f"Bearish FVG at {fvg_timestamp} matches swing low at {swing['timestamp']} (price diff: {price_diff:.2f} pts)")
                    return True
    
    return False

