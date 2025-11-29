# Swing High/Low Detection Algorithm Explained

## Overview

Swing highs and lows are key price points where the market reverses direction. They represent **liquidity levels** where traders often place stop-loss orders, making them important for the iFVG liquidity filter.

## Algorithm Logic

### Swing High Detection

A **Swing High** is a candle where:
1. The candle's **high price** is higher than all highs in the `lookback` candles **before** it
2. The candle's **high price** is higher than all highs in the `lookback` candles **after** it

**Formula:**
```
Swing High at candle[i] IF:
  high[i] > max(high[i-lookback : i-1])  AND
  high[i] > max(high[i+1 : i+lookback])
```

### Swing Low Detection

A **Swing Low** is a candle where:
1. The candle's **low price** is lower than all lows in the `lookback` candles **before** it
2. The candle's **low price** is lower than all lows in the `lookback` candles **after** it

**Formula:**
```
Swing Low at candle[i] IF:
  low[i] < min(low[i-lookback : i-1])  AND
  low[i] < min(low[i+1 : i+lookback])
```

## Visual Example

### Example 1: Swing High with lookback=5

```
Price
  |
  |                    ╱╲
  |                   ╱  ╲
  |                  ╱    ╲
  |                 ╱      ╲
  |                ╱        ╲
  |               ╱          ╲
  |              ╱            ╲
  |             ╱              ╲
  |            ╱                ╲
  |           ╱                  ╲
  |          ╱                    ╲
  |         ╱                      ╲
  |        ╱                        ╲
  |       ╱                          ╲
  |      ╱                            ╲
  |     ╱                              ╲
  |    ╱                                ╲
  |   ╱                                  ╲
  |  ╱                                    ╲
  | ╱                                      ╲
  |╱                                        ╲
  └─────────────────────────────────────────────> Time
   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14

Candle indices: 0, 1, 2, 3, 4, [5], 6, 7, 8, 9, 10
                 ↑  ↑  ↑  ↑  ↑   ↑   ↑  ↑  ↑  ↑  ↑
                 Left lookback (5 candles)  Right lookback (5 candles)
```

**At candle index 5:**
- **Current high** = 105.0
- **Left highs** (candles 0-4): [100, 101, 102, 103, 104] → **max = 104.0**
- **Right highs** (candles 6-10): [104, 103, 102, 101, 100] → **max = 104.0**

**Check:**
- `105.0 > 104.0` ✅ (higher than left)
- `105.0 > 104.0` ✅ (higher than right)

**Result:** ✅ **Swing High detected at candle 5**

### Example 2: Swing Low with lookback=5

```
Price
  |
  |                                        ╱╲
  |                                       ╱  ╲
  |                                      ╱    ╲
  |                                     ╱      ╲
  |                                    ╱        ╲
  |                                   ╱          ╲
  |                                  ╱            ╲
  |                                 ╱              ╲
  |                                ╱                ╲
  |                               ╱                  ╲
  |                              ╱                    ╲
  |                             ╱                      ╲
  |                            ╱                        ╲
  |                           ╱                          ╲
  |                          ╱                            ╲
  |                         ╱                              ╲
  |                        ╱                                ╲
  |                       ╱                                  ╲
  |                      ╱                                    ╲
  |                     ╱                                      ╲
  |                    ╱                                        ╲
  |                   ╱                                          ╲
  |                  ╱                                            ╲
  |                 ╱                                              ╲
  |                ╱                                                ╲
  |               ╱                                                  ╲
  |              ╱                                                    ╲
  |             ╱                                                      ╲
  |            ╱                                                        ╲
  |           ╱                                                          ╲
  |          ╱                                                            ╲
  |         ╱                                                              ╲
  |        ╱                                                                ╲
  |       ╱                                                                  ╲
  |      ╱                                                                    ╲
  |     ╱                                                                      ╲
  |    ╱                                                                        ╲
  |   ╱                                                                          ╲
  |  ╱                                                                            ╲
  | ╱                                                                              ╲
  └─────────────────────────────────────────────────────────────────────────────> Time
   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14

Candle indices: 0, 1, 2, 3, 4, [5], 6, 7, 8, 9, 10
                 ↑  ↑  ↑  ↑  ↑   ↑   ↑  ↑  ↑  ↑  ↑
                 Left lookback (5 candles)  Right lookback (5 candles)
```

**At candle index 5:**
- **Current low** = 95.0
- **Left lows** (candles 0-4): [100, 99, 98, 97, 96] → **min = 96.0**
- **Right lows** (candles 6-10): [96, 97, 98, 99, 100] → **min = 96.0**

**Check:**
- `95.0 < 96.0` ✅ (lower than left)
- `95.0 < 96.0` ✅ (lower than right)

**Result:** ✅ **Swing Low detected at candle 5**

## Step-by-Step Process

### 1. Data Preparation

```python
# Sort candles by timestamp (oldest to newest)
df = candles_df.sort_values('ts_ny').reset_index(drop=True)

# Need at least (lookback * 2 + 1) candles
# Example: lookback=5 needs at least 11 candles
```

### 2. Iteration

```python
# Start from index 'lookback' (can't check before this)
# End at index 'len(df) - lookback' (can't check after this)
for i in range(lookback, len(df) - lookback):
    # Check swing high
    # Check swing low
```

### 3. Swing High Check

```python
# Get current candle's high
current_high = df.loc[i, 'high_price']

# Get maximum high from left side (previous 'lookback' candles)
left_highs = df.loc[i-lookback:i-1, 'high_price'].max()

# Get maximum high from right side (next 'lookback' candles)
right_highs = df.loc[i+1:i+lookback, 'high_price'].max()

# Is it a swing high?
if current_high > left_highs and current_high > right_highs:
    # Yes! Record it
    swings.append({
        'timestamp': df.loc[i, 'ts_ny'],
        'price': current_high,
        'type': 'high'
    })
```

### 4. Swing Low Check

```python
# Get current candle's low
current_low = df.loc[i, 'low_price']

# Get minimum low from left side
left_lows = df.loc[i-lookback:i-1, 'low_price'].min()

# Get minimum low from right side
right_lows = df.loc[i+1:i+lookback, 'low_price'].min()

# Is it a swing low?
if current_low < left_lows and current_low < right_lows:
    # Yes! Record it
    swings.append({
        'timestamp': df.loc[i, 'ts_ny'],
        'price': current_low,
        'type': 'low'
    })
```

## Real-World Example

### Scenario: 1-Hour Timeframe, lookback=5

**Candle Data (1-hour candles):**

| Index | Time | High | Low | Close |
|-------|------|------|-----|-------|
| 0 | 09:00 | 100.0 | 99.0 | 99.5 |
| 1 | 10:00 | 101.0 | 100.0 | 100.5 |
| 2 | 11:00 | 102.0 | 101.0 | 101.5 |
| 3 | 12:00 | 103.0 | 102.0 | 102.5 |
| 4 | 13:00 | 104.0 | 103.0 | 103.5 |
| **5** | **14:00** | **105.0** | **104.0** | **104.5** |
| 6 | 15:00 | 104.0 | 103.0 | 103.5 |
| 7 | 16:00 | 103.0 | 102.0 | 102.5 |
| 8 | 17:00 | 102.0 | 101.0 | 101.5 |
| 9 | 18:00 | 101.0 | 100.0 | 100.5 |
| 10 | 19:00 | 100.0 | 99.0 | 99.5 |

**Checking candle 5 (14:00) for Swing High:**

1. **Current high**: 105.0
2. **Left side** (candles 0-4): Highs = [100.0, 101.0, 102.0, 103.0, 104.0]
   - **Max left**: 104.0
3. **Right side** (candles 6-10): Highs = [104.0, 103.0, 102.0, 101.0, 100.0]
   - **Max right**: 104.0
4. **Comparison**:
   - `105.0 > 104.0` ✅ (higher than all left)
   - `105.0 > 104.0` ✅ (higher than all right)
5. **Result**: ✅ **Swing High at 14:00, price = 105.0**

## Why This Matters for iFVG

### Liquidity Levels

Swing highs and lows represent **liquidity levels** where:
- Traders place stop-loss orders
- Price often reverses after touching these levels
- FVGs that form at these levels are more significant

### Matching FVG to Swing Levels

**Bullish FVG** (price gaps up):
- FVG's `gap_low` should be near a **swing high**
- This means price took out the swing high (liquidity sweep)
- Then gapped up, creating the FVG

**Bearish FVG** (price gaps down):
- FVG's `gap_high` should be near a **swing low**
- This means price took out the swing low (liquidity sweep)
- Then gapped down, creating the FVG

## Parameters

### `lookback` Parameter

- **Default**: 5 candles
- **Range**: 1-50 candles
- **Effect**:
  - **Smaller lookback (1-3)**: More sensitive, detects more swings (including minor ones)
  - **Larger lookback (10-20)**: Less sensitive, detects only major swings
  - **Recommended**: 5-10 for most timeframes

### Timeframe Selection

- **15m/30m**: Good for intraday swings
- **1h**: Balanced - detects significant intraday levels
- **4h**: Major daily swings
- **1d**: Weekly/monthly major levels

**Recommendation**: Use `1h` or `4h` for liquidity filter to focus on significant levels.

## Edge Cases

### 1. Insufficient Candles

```python
if len(candles_df) < (lookback * 2 + 1):
    # Can't detect swings - need at least (lookback * 2 + 1) candles
    return []
```

**Example**: With `lookback=5`, need at least 11 candles.

### 2. Multiple Swings

The algorithm can detect multiple swing highs and lows in the same dataset. Each swing is independent.

### 3. Equal Values

If `current_high == max(left_highs)` or `current_high == max(right_highs)`, it's **NOT** a swing high (must be strictly greater).

Similarly for swing lows (must be strictly less).

## Performance Considerations

- **Time Complexity**: O(n × lookback) where n = number of candles
- **Space Complexity**: O(n) for storing swing points
- **Optimization**: For large datasets, consider caching swing points

## Code Location

The implementation is in:
- **File**: `backend/app/services/fvg_detector.py`
- **Function**: `detect_swing_highs_lows()`
- **Lines**: 234-291

## Summary

**Swing High**: A price point that is the highest within `lookback` candles on both sides.

**Swing Low**: A price point that is the lowest within `lookback` candles on both sides.

**Purpose**: Identify liquidity levels where price reversals are more likely, improving FVG signal quality.

