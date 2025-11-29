# Trend Trading Implementation - Comprehensive Explanation

## Overview
Trend trading filters trades based on moving average (MA) trend direction. It only allows trades that align with the current trend, potentially improving win rates by trading with the market momentum.

## How It Works

### 1. **Moving Average Calculation**
- **Timeframe**: Configurable (5m, 15m, 30m, 1h) - determines the granularity of trend detection
- **Period**: Configurable (default: 20) - number of candles used to calculate the MA
- **Type**: 
  - **SMA (Simple Moving Average)**: Average of last N close prices
  - **EMA (Exponential Moving Average)**: Weighted average giving more weight to recent prices (approximated using window function)

### 2. **Trend Direction Determination**
For each candle in the trend timeframe:
- **Bullish Trend**: `close_price > ma_value` (price above moving average)
- **Bearish Trend**: `close_price < ma_value` (price below moving average)
- **Neutral**: `close_price = ma_value` (rare, price equals MA)

### 3. **Trend Lookup at Entry Time**
When an entry opportunity occurs:
- The system looks up the most recent trend direction **at or before** the entry time
- Uses a LATERAL JOIN to find the latest trend data point for that entry
- This ensures we're using the trend that was known at the time of entry

### 4. **Trade Filtering**

#### **Strict Mode** (default: ON)
- **Bullish trades**: Only allowed when trend is bullish
- **Bearish trades**: Only allowed when trend is bearish
- **Auto/Neutral trades**: Allowed when trend exists (any direction)

#### **Non-Strict Mode** (default: OFF)
- Only requires that trend direction exists (not NULL)
- Allows counter-trend trades if direction is explicitly specified
- Less restrictive filtering

## SQL Implementation Flow

```
1. trend_data CTE:
   - Scans trend timeframe data (e.g., 15m candles)
   - Calculates moving average using window function
   - Filtered by year range for performance

2. trend_at_entry CTE:
   - Determines trend direction (bullish/bearish/neutral)
   - Uses ROW_NUMBER() to get one trend value per time point

3. trend_at_entry_filtered CTE:
   - Filters to unique trend values per time

4. entries CTE:
   - Finds all potential entry points (5m candles in entry time window)

5. setup CTE:
   - Joins entries with trend data using LATERAL JOIN
   - Filters entries based on trend direction and strictness mode
   - Only entries that pass the trend filter proceed

6. path CTE:
   - Tracks price movement after entry (1m candles)
   - Uses optimized timestamp comparison

7. hits CTE:
   - Determines if TP or SL was hit first

8. Final aggregation:
   - Groups results by strategy/year/month/day
```

## Performance Characteristics

### Optimizations Applied:
1. **Year Filtering**: `trend_data` CTE is filtered by year range to reduce data scanned
2. **Optimized LATERAL JOIN**: Uses `trading_date` instead of `DATE(ts_ny)` for faster lookup
3. **Window Functions**: Uses efficient window functions for MA calculation
4. **Indexed Lookups**: Leverages existing database indexes on timeframe and timestamp

### Performance Impact:
- **Without Trend**: ~1 second for single year
- **With Trend**: ~2-5 seconds for single year (depends on trend timeframe and period)
- **Additional Overhead**: 
  - One extra CTE scan (trend_data)
  - LATERAL JOIN per entry (typically 50-200 entries per day)
  - Trend filtering reduces number of trades, which can actually speed up the `path` CTE

### Why It Doesn't Add Considerable Runtime:
1. **Year Filtering**: Only scans trend data for the requested year range
2. **Efficient Window Functions**: PostgreSQL optimizes window functions well
3. **Early Filtering**: Trend filter reduces entries before expensive `path` CTE
4. **LATERAL JOIN Optimization**: Uses indexed date comparison instead of function calls

## Configuration Parameters

- **trend_enabled**: Enable/disable trend filtering (boolean)
- **trend_timeframe**: Timeframe for trend calculation ('5m', '15m', '30m', '1h')
- **trend_period**: Number of periods for MA calculation (default: 20)
- **trend_type**: 'sma' or 'ema' (default: 'sma')
- **trend_strict**: Strict mode - only trade with trend (default: true)

## Example Scenarios

### Scenario 1: Bullish Entry with Bullish Trend (Strict Mode)
- Entry direction: `bullish`
- Trend at entry: `bullish`
- **Result**: ✅ Trade allowed (trend matches direction)

### Scenario 2: Bullish Entry with Bearish Trend (Strict Mode)
- Entry direction: `bullish`
- Trend at entry: `bearish`
- **Result**: ❌ Trade filtered out (trend doesn't match)

### Scenario 3: Bullish Entry with Bearish Trend (Non-Strict Mode)
- Entry direction: `bullish`
- Trend at entry: `bearish`
- **Result**: ✅ Trade allowed (trend exists, non-strict allows counter-trend)

### Scenario 4: Auto Direction with Any Trend
- Entry direction: `auto` or `null`
- Trend at entry: `bullish` or `bearish`
- **Result**: ✅ Trade allowed (any trend direction is acceptable)

## Integration with Existing Logic

### No Conflicts:
- Trend filtering happens **before** the `path` CTE (price tracking)
- It only filters entries, doesn't change TP/SL logic
- Direction parameter still works - trend is an additional filter
- All existing optimizations (timestamp comparison, year filtering) remain

### Compatibility:
- Works with all grouping types (hierarchical, by_year, by_dow, by_candle, trades)
- Works with both flat trades and grouped results views
- Can be enabled/disabled per scenario
- Default is OFF (disabled) for backward compatibility

## Performance Notes

The LATERAL JOIN executes once per entry (not per 1m candle), so it's relatively efficient. However, for very large datasets or multiple years, you may see:
- 2-5x query time increase when trend is enabled
- This is acceptable because:
  1. Trend filtering reduces the number of trades to track
  2. The `path` CTE becomes faster with fewer entries
  3. Overall, the trade-off is usually worth it for better signal quality

## Future Optimizations (if needed)

1. **Materialized Trend Data**: Pre-calculate trend for common timeframes
2. **Index on trend_at_entry_filtered**: Add index on (trading_date, ts_ny) if needed
3. **Batch Trend Lookup**: Use window function instead of LATERAL JOIN
4. **Caching**: Cache trend calculations for repeated queries

