"""Unit tests for iFVG FVG detector functions."""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.services.fvg_detector import (
    detect_fvgs,
    detect_inversions,
    compute_rr,
    get_timeframe_minutes,
    detect_swing_highs_lows,
    is_fvg_at_liquidity_level
)


class TestDetectFVGs:
    """Test FVG detection logic."""
    
    def test_bullish_fvg_detection(self):
        """Test detection of bullish FVG (low[i] > high[i-2])."""
        # Create test data with a bullish FVG
        # Candle 0: high=100
        # Candle 1: high=101
        # Candle 2: low=102 (gap: 102 > 100, bullish FVG)
        timestamps = [
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 5),
            datetime(2024, 1, 1, 9, 10),
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [99.0, 100.5, 102.5],
            'high_price': [100.0, 101.0, 103.0],
            'low_price': [98.0, 100.0, 102.0],
            'close_price': [99.5, 100.8, 102.8]
        })
        
        fvgs = detect_fvgs(df, '5m')
        
        assert len(fvgs) == 1
        assert fvgs[0]['direction'] == 'bullish'
        assert fvgs[0]['gap_low'] == 100.0  # high of candle i-2
        assert fvgs[0]['gap_high'] == 102.0  # low of candle i
        assert fvgs[0]['fvg_size'] == 2.0
        assert fvgs[0]['timestamp'] == timestamps[2]
    
    def test_bearish_fvg_detection(self):
        """Test detection of bearish FVG (high[i] < low[i-2])."""
        # Create test data with a bearish FVG
        # Candle 0: low=100
        # Candle 1: low=99
        # Candle 2: high=98 (gap: 98 < 100, bearish FVG)
        timestamps = [
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 5),
            datetime(2024, 1, 1, 9, 10),
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [101.0, 99.5, 98.5],
            'high_price': [102.0, 100.0, 98.0],
            'low_price': [100.0, 99.0, 97.0],
            'close_price': [101.5, 99.8, 97.8]
        })
        
        fvgs = detect_fvgs(df, '5m')
        
        assert len(fvgs) == 1
        assert fvgs[0]['direction'] == 'bearish'
        assert fvgs[0]['gap_low'] == 98.0  # high of candle i
        assert fvgs[0]['gap_high'] == 100.0  # low of candle i-2
        assert fvgs[0]['fvg_size'] == 2.0
        assert fvgs[0]['timestamp'] == timestamps[2]
    
    def test_no_fvg_detected(self):
        """Test when no FVG is present."""
        timestamps = [
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 5),
            datetime(2024, 1, 1, 9, 10),
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [100.0, 100.5, 100.8],
            'high_price': [101.0, 101.5, 101.8],
            'low_price': [99.0, 99.5, 99.8],
            'close_price': [100.5, 101.0, 101.3]
        })
        
        fvgs = detect_fvgs(df, '5m')
        assert len(fvgs) == 0
    
    def test_insufficient_candles(self):
        """Test with insufficient candles (< 3)."""
        df = pd.DataFrame({
            'ts_ny': [datetime(2024, 1, 1, 9, 0)],
            'open_price': [100.0],
            'high_price': [101.0],
            'low_price': [99.0],
            'close_price': [100.5]
        })
        
        fvgs = detect_fvgs(df, '5m')
        assert len(fvgs) == 0
    
    def test_multiple_fvgs(self):
        """Test detection of multiple FVGs."""
        timestamps = [
            datetime(2024, 1, 1, 9, 0),
            datetime(2024, 1, 1, 9, 5),
            datetime(2024, 1, 1, 9, 10),  # Bullish FVG
            datetime(2024, 1, 1, 9, 15),
            datetime(2024, 1, 1, 9, 20),  # Bearish FVG
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [99.0, 100.5, 102.5, 101.0, 98.5],
            'high_price': [100.0, 101.0, 103.0, 101.5, 98.0],
            'low_price': [98.0, 100.0, 102.0, 100.5, 97.0],
            'close_price': [99.5, 100.8, 102.8, 101.2, 97.8]
        })
        
        fvgs = detect_fvgs(df, '5m')
        
        assert len(fvgs) == 2
        assert fvgs[0]['direction'] == 'bullish'
        assert fvgs[1]['direction'] == 'bearish'


class TestDetectInversions:
    """Test inversion detection logic."""
    
    def test_bullish_fvg_inversion(self):
        """Test inversion of bullish FVG (bearish candle closes below gap_low)."""
        # Create bullish FVG
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 10),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0,
            'fvg_size': 2.0
        }
        
        # Create candles with inversion (bearish candle closes below gap_low)
        timestamps = [
            datetime(2024, 1, 1, 9, 10),  # FVG timestamp
            datetime(2024, 1, 1, 9, 15),
            datetime(2024, 1, 1, 9, 20),  # Inversion: close=99.5 < gap_low=100.0
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [102.5, 101.0, 100.5],
            'high_price': [103.0, 101.5, 100.8],
            'low_price': [102.0, 100.5, 99.0],
            'close_price': [102.8, 101.2, 99.5]  # Bearish candle (close < open)
        })
        
        inversions = detect_inversions([fvg], df, wait_candles=24, fvg_timeframe_minutes=5)
        
        assert len(inversions) == 1
        assert inversions[0]['fvg_ts'] == fvg['timestamp']
        assert inversions[0]['inv_ts'] == timestamps[2]
        assert inversions[0]['inv_dir'] == 'bearish'
        assert inversions[0]['gap_low'] == 100.0
        assert inversions[0]['gap_high'] == 102.0
    
    def test_bearish_fvg_inversion(self):
        """Test inversion of bearish FVG (bullish candle closes above gap_high)."""
        # Create bearish FVG
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 10),
            'direction': 'bearish',
            'gap_low': 98.0,
            'gap_high': 100.0,
            'fvg_size': 2.0
        }
        
        # Create candles with inversion (bullish candle closes above gap_high)
        timestamps = [
            datetime(2024, 1, 1, 9, 10),  # FVG timestamp
            datetime(2024, 1, 1, 9, 15),
            datetime(2024, 1, 1, 9, 20),  # Inversion: close=100.5 > gap_high=100.0
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [98.5, 99.0, 99.5],
            'high_price': [98.0, 99.5, 100.8],
            'low_price': [97.0, 98.5, 99.0],
            'close_price': [97.8, 99.2, 100.5]  # Bullish candle (close > open)
        })
        
        inversions = detect_inversions([fvg], df, wait_candles=24, fvg_timeframe_minutes=5)
        
        assert len(inversions) == 1
        assert inversions[0]['inv_dir'] == 'bullish'
        assert inversions[0]['inv_ts'] == timestamps[2]
    
    def test_no_inversion_within_wait_window(self):
        """Test when no inversion occurs within wait window."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 10),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0,
            'fvg_size': 2.0
        }
        
        # Create candles but none close below gap_low
        timestamps = [
            datetime(2024, 1, 1, 9, 10),
            datetime(2024, 1, 1, 9, 15),
            datetime(2024, 1, 1, 9, 20),
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [102.5, 101.0, 101.5],
            'high_price': [103.0, 101.5, 102.0],
            'low_price': [102.0, 100.5, 101.0],
            'close_price': [102.8, 101.2, 101.8]  # All above gap_low
        })
        
        inversions = detect_inversions([fvg], df, wait_candles=2, fvg_timeframe_minutes=5)
        
        assert len(inversions) == 0
    
    def test_inversion_timeout(self):
        """Test that inversion must occur within wait_candles window."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 0),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0,
            'fvg_size': 2.0
        }
        
        # Inversion occurs after wait window (wait_candles=2 = 10 minutes)
        timestamps = [
            datetime(2024, 1, 1, 9, 0),   # FVG
            datetime(2024, 1, 1, 9, 5),
            datetime(2024, 1, 1, 9, 10),  # End of wait window
            datetime(2024, 1, 1, 9, 15),  # Inversion (too late)
        ]
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'open_price': [102.5, 101.0, 101.5, 100.5],
            'high_price': [103.0, 101.5, 102.0, 100.8],
            'low_price': [102.0, 100.5, 101.0, 99.0],
            'close_price': [102.8, 101.2, 101.8, 99.5]  # Inversion at 9:15
        })
        
        inversions = detect_inversions([fvg], df, wait_candles=2, fvg_timeframe_minutes=5)
        
        assert len(inversions) == 0  # Inversion too late


class TestComputeRR:
    """Test Risk-Reward calculation logic."""
    
    def test_fixed_rr_bullish(self):
        """Test fixed RR mode for bullish trade."""
        entry_price = 100.0
        fvg_low = 98.0
        fvg_high = 102.0
        direction = 'bullish'
        params = {
            'use_adaptive_rr': False,
            'target_pts': 50.0,
            'stop_pts': 25.0
        }
        
        stop_loss, take_profit = compute_rr(entry_price, fvg_low, fvg_high, direction, params)
        
        assert stop_loss == 75.0  # entry - stop_pts
        assert take_profit == 150.0  # entry + target_pts
    
    def test_fixed_rr_bearish(self):
        """Test fixed RR mode for bearish trade."""
        entry_price = 100.0
        fvg_low = 98.0
        fvg_high = 102.0
        direction = 'bearish'
        params = {
            'use_adaptive_rr': False,
            'target_pts': 50.0,
            'stop_pts': 25.0
        }
        
        stop_loss, take_profit = compute_rr(entry_price, fvg_low, fvg_high, direction, params)
        
        assert stop_loss == 125.0  # entry + stop_pts
        assert take_profit == 50.0  # entry - target_pts
    
    def test_adaptive_rr_bullish(self):
        """Test adaptive RR mode for bullish trade."""
        entry_price = 100.0
        fvg_low = 95.0
        fvg_high = 100.0  # FVG size = 5.0
        direction = 'bullish'
        params = {
            'use_adaptive_rr': True,
            'extra_margin_pts': 5.0,
            'rr_multiple': 2.0
        }
        
        stop_loss, take_profit = compute_rr(entry_price, fvg_low, fvg_high, direction, params)
        
        # SL = gap_low - extra_margin = 95.0 - 5.0 = 90.0
        # Risk = extra_margin + fvg_size = 5.0 + 5.0 = 10.0
        # TP = entry + (risk * rr_multiple) = 100.0 + (10.0 * 2.0) = 120.0
        assert stop_loss == 90.0
        assert take_profit == 120.0
    
    def test_adaptive_rr_bearish(self):
        """Test adaptive RR mode for bearish trade."""
        entry_price = 100.0
        fvg_low = 100.0
        fvg_high = 105.0  # FVG size = 5.0
        direction = 'bearish'
        params = {
            'use_adaptive_rr': True,
            'extra_margin_pts': 5.0,
            'rr_multiple': 2.0
        }
        
        stop_loss, take_profit = compute_rr(entry_price, fvg_low, fvg_high, direction, params)
        
        # SL = gap_high + extra_margin = 105.0 + 5.0 = 110.0
        # Risk = extra_margin + fvg_size = 5.0 + 5.0 = 10.0
        # TP = entry - (risk * rr_multiple) = 100.0 - (10.0 * 2.0) = 80.0
        assert stop_loss == 110.0
        assert take_profit == 80.0


class TestDetectSwingHighsLows:
    """Test swing high/low detection logic."""
    
    def test_swing_high_detection(self):
        """Test detection of swing high."""
        # Create data with a clear swing high at index 5
        # Pattern: low -> high -> low
        timestamps = [datetime(2024, 1, 1, 9, i*5) for i in range(11)]
        highs = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.0, 103.0, 102.0, 101.0, 100.0]
        lows = [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 103.0, 102.0, 101.0, 100.0, 99.0]
        
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'high_price': highs,
            'low_price': lows
        })
        
        swings = detect_swing_highs_lows(df, '15m', lookback=5)
        
        # Should detect swing high at index 5 (105.0)
        assert len(swings) >= 1
        swing_highs = [s for s in swings if s['type'] == 'high']
        assert len(swing_highs) >= 1
        assert any(s['price'] == 105.0 for s in swing_highs)
    
    def test_swing_low_detection(self):
        """Test detection of swing low."""
        # Create data with a clear swing low at index 5
        # Pattern: high -> low -> high
        timestamps = [datetime(2024, 1, 1, 9, i*5) for i in range(11)]
        highs = [105.0, 104.0, 103.0, 102.0, 101.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
        lows = [104.0, 103.0, 102.0, 101.0, 100.0, 99.0, 100.0, 101.0, 102.0, 103.0, 104.0]
        
        df = pd.DataFrame({
            'ts_ny': timestamps,
            'high_price': highs,
            'low_price': lows
        })
        
        swings = detect_swing_highs_lows(df, '15m', lookback=5)
        
        # Should detect swing low at index 5 (99.0)
        assert len(swings) >= 1
        swing_lows = [s for s in swings if s['type'] == 'low']
        assert len(swing_lows) >= 1
        assert any(s['price'] == 99.0 for s in swing_lows)
    
    def test_insufficient_candles_for_swing(self):
        """Test with insufficient candles for swing detection."""
        df = pd.DataFrame({
            'ts_ny': [datetime(2024, 1, 1, 9, i*5) for i in range(5)],  # Only 5 candles, need 11 for lookback=5
            'high_price': [100.0, 101.0, 102.0, 101.0, 100.0],
            'low_price': [99.0, 100.0, 101.0, 100.0, 99.0]
        })
        
        swings = detect_swing_highs_lows(df, '15m', lookback=5)
        
        assert len(swings) == 0


class TestIsFVGAtLiquidityLevel:
    """Test liquidity level matching logic."""
    
    def test_bullish_fvg_matches_swing_high(self):
        """Test bullish FVG matching swing high."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 30),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0
        }
        
        swing_points = [
            {
                'timestamp': datetime(2024, 1, 1, 9, 0),
                'price': 100.2,  # Within tolerance of gap_low
                'type': 'high'
            }
        ]
        
        result = is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts=5.0)
        
        assert result is True
    
    def test_bearish_fvg_matches_swing_low(self):
        """Test bearish FVG matching swing low."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 30),
            'direction': 'bearish',
            'gap_low': 98.0,
            'gap_high': 100.0
        }
        
        swing_points = [
            {
                'timestamp': datetime(2024, 1, 1, 9, 0),
                'price': 100.2,  # Within tolerance of gap_high
                'type': 'low'
            }
        ]
        
        result = is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts=5.0)
        
        assert result is True
    
    def test_fvg_outside_tolerance(self):
        """Test FVG that doesn't match due to tolerance."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 30),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0
        }
        
        swing_points = [
            {
                'timestamp': datetime(2024, 1, 1, 9, 0),
                'price': 110.0,  # Too far from gap_low
                'type': 'high'
            }
        ]
        
        result = is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts=5.0)
        
        assert result is False
    
    def test_fvg_outside_time_window(self):
        """Test FVG that doesn't match due to time window."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 0),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0
        }
        
        swing_points = [
            {
                'timestamp': datetime(2024, 1, 1, 11, 0),  # 2 hours later (outside 1-hour window)
                'price': 100.2,
                'type': 'high'
            }
        ]
        
        result = is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts=5.0)
        
        assert result is False
    
    def test_wrong_swing_type(self):
        """Test that bullish FVG doesn't match swing low."""
        fvg = {
            'timestamp': datetime(2024, 1, 1, 9, 30),
            'direction': 'bullish',
            'gap_low': 100.0,
            'gap_high': 102.0
        }
        
        swing_points = [
            {
                'timestamp': datetime(2024, 1, 1, 9, 0),
                'price': 100.2,
                'type': 'low'  # Wrong type (should be 'high')
            }
        ]
        
        result = is_fvg_at_liquidity_level(fvg, swing_points, tolerance_pts=5.0)
        
        assert result is False


class TestGetTimeframeMinutes:
    """Test timeframe conversion."""
    
    def test_standard_timeframes(self):
        """Test standard timeframe conversions."""
        assert get_timeframe_minutes('1m') == 1
        assert get_timeframe_minutes('5m') == 5
        assert get_timeframe_minutes('15m') == 15
        assert get_timeframe_minutes('30m') == 30
        assert get_timeframe_minutes('1h') == 60
        assert get_timeframe_minutes('4h') == 240
        assert get_timeframe_minutes('1d') == 1440
    
    def test_unknown_timeframe_defaults(self):
        """Test that unknown timeframe defaults to 5 minutes."""
        assert get_timeframe_minutes('unknown') == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

