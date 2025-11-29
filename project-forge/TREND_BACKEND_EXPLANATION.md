# Trend Following Parameters - Backend Implementation

## Overview
Trend following filters trades based on moving average (MA) trend direction. The backend implements this through SQL template rendering and execution.

## Parameter Flow

### 1. **Frontend → Backend API**
```
Frontend (chat/page.tsx)
  ↓
  trendEnabled: boolean
  trendTimeframe: '15m'
  trendPeriod: 20
  trendType: 'sma' | 'ema'
  trendStrict: boolean
  ↓
Backend API (routes_ai.py or routes_backtest.py)
  ↓
ScenarioParams model
```

### 2. **Backend API → Scenario Storage**
Parameters are stored in `BacktestScenario.params` (JSON field):
```python
{
  "trend_enabled": true,
  "trend_timeframe": "15m",
  "trend_period": 20,
  "trend_type": "sma",
  "trend_strict": true,
  ...other params...
}
```

### 3. **Scenario Execution → SQL Template Rendering**

**Location**: `backend/app/services/runner.py` → `run_backtest_scenario()`

```python
# Extract and validate trend_enabled
trend_enabled_val = params.get("trend_enabled")
if trend_enabled_val is None:
    trend_enabled_val = False
else:
    trend_enabled_val = bool(trend_enabled_val)

# Build template parameters
template_params = {
    # ... other params ...
    "trend_enabled": trend_enabled_val,
    "trend_timeframe": params.get("trend_timeframe", "15m") if trend_enabled_val else "15m",
    "trend_period": int(params.get("trend_period", 20)) if trend_enabled_val else 20,
    "trend_type": params.get("trend_type", "sma") if trend_enabled_val else "sma",
    "trend_strict": params.get("trend_strict", True) if trend_enabled_val else True,
}

# Render SQL template (Jinja2)
sql = template_engine.render_hierarchical(template_params)
```

**Key Points**:
- `trend_enabled` is always converted to boolean (never None)
- Defaults are applied if parameters are missing
- Parameters are passed to Jinja2 template engine

## SQL Template Implementation

**Location**: `backend/app/sql/base_templates/hierarchical.sql.j2` (and 4 other templates)

### Step 1: Calculate Moving Average (if trend_enabled)

```sql
{% if trend_enabled %}
trend_data AS (
  SELECT
    (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
    close_price,
    -- SMA or EMA calculation
    AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN {{ trend_period - 1 }} PRECEDING AND CURRENT ROW
    ) AS ma_value
  FROM market.ohlcv_data
  WHERE timeframe = '{{ trend_timeframe }}'  -- e.g., '15m'
    AND DATE_PART('year', ...) BETWEEN {{ year_start }} AND {{ year_end }}
),
```

**What this does**:
- Scans `market.ohlcv_data` for the trend timeframe (e.g., 15m candles)
- Calculates moving average using window function
- `ROWS BETWEEN {{ trend_period - 1 }} PRECEDING` = last N candles (e.g., 19 preceding + current = 20 period MA)
- Filters by year range for performance

**Example**: If `trend_period = 20` and `trend_timeframe = '15m'`:
- Calculates 20-period SMA on 15-minute candles
- Each row gets: `AVG(close_price) OVER (ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)`

### Step 2: Determine Trend Direction

```sql
trend_at_entry AS (
  SELECT 
    DATE(ts_ny) AS trading_date,
    ts_ny,
    ma_value,
    close_price,
    CASE 
      WHEN close_price > ma_value THEN 'bullish'
      WHEN close_price < ma_value THEN 'bearish'
      ELSE 'neutral'
    END AS trend_direction,
    ROW_NUMBER() OVER (PARTITION BY DATE(ts_ny), ts_ny::time ORDER BY ts_ny DESC) AS rn
  FROM trend_data
),
trend_at_entry_filtered AS (
  SELECT trading_date, ts_ny, ma_value, close_price, trend_direction
  FROM trend_at_entry
  WHERE rn = 1
),
```

**What this does**:
- For each candle in `trend_data`:
  - If `close_price > ma_value` → trend = 'bullish'
  - If `close_price < ma_value` → trend = 'bearish'
  - If `close_price = ma_value` → trend = 'neutral' (rare)
- `ROW_NUMBER()` ensures one trend value per unique time
- `trend_at_entry_filtered` removes duplicates

### Step 3: Find Entry Points (5m candles)

```sql
entries AS (
  SELECT DATE(f.ts_ny) trading_date, f.open_price entry_price, f.ts_ny entry_ts_ny
  FROM five f
  WHERE f.ts_ny::time >= TIME '{{ entry_time_start }}'
    AND f.ts_ny::time <= TIME '{{ entry_time_end }}'
),
```

**What this does**:
- Finds all 5-minute candles in the entry time window (e.g., 09:00-10:00)
- These are potential trade entry points

### Step 4: Join Entries with Trend Data

```sql
setup AS (
  SELECT 
    e.*, 
    {% if direction %}
    CAST('{{ direction }}' AS TEXT) AS direction{% if trend_enabled %},
    t.trend_direction
    {% endif %}
    {% else %}
    'neutral' AS direction{% if trend_enabled %},
    t.trend_direction
    {% endif %}
    {% endif %}
  FROM entries e
  {% if trend_enabled %}
  -- LATERAL JOIN: Find trend at entry time
  LEFT JOIN LATERAL (
    SELECT trend_direction
    FROM trend_at_entry_filtered tae
    WHERE tae.trading_date = DATE(e.entry_ts_ny)
      AND tae.ts_ny <= e.entry_ts_ny
    ORDER BY tae.ts_ny DESC
    LIMIT 1
  ) t ON true
  {% endif %}
  WHERE DATE_PART('year', e.trading_date) BETWEEN {{ year_start }} AND {{ year_end }}
    {% if trend_enabled %}
    -- Apply trend filter
    {% if trend_strict %}
    -- Strict mode: only trade in the direction of the trend
    AND (
      {% if direction %}
      (CAST('{{ direction }}' AS TEXT) = 'bullish' AND t.trend_direction = 'bullish')
      OR (CAST('{{ direction }}' AS TEXT) = 'bearish' AND t.trend_direction = 'bearish')
      {% else %}
      -- Auto/neutral direction: allow any trend direction
      t.trend_direction IS NOT NULL
      {% endif %}
    )
    {% else %}
    -- Non-strict mode: allow counter-trend if direction is explicitly specified
    AND t.trend_direction IS NOT NULL
    {% endif %}
    {% endif %}
),
```

**What this does**:

#### LATERAL JOIN Explanation:
- For each entry (5m candle), finds the most recent trend data point **at or before** that entry time
- Uses `LATERAL JOIN` to look up trend for each entry individually
- `WHERE tae.trading_date = DATE(e.entry_ts_ny)` = same trading day
- `AND tae.ts_ny <= e.entry_ts_ny` = trend data before/at entry time
- `ORDER BY tae.ts_ny DESC LIMIT 1` = most recent trend

**Example**:
- Entry time: `2024-01-15 09:30:00` (5m candle)
- Looks for trend data from 15m candles: `2024-01-15 09:15:00`, `09:30:00`, etc.
- Finds most recent: `09:30:00` with trend = 'bullish'
- Result: Entry gets `trend_direction = 'bullish'`

#### Trend Filtering Logic:

**Strict Mode** (`trend_strict = true`):
```sql
AND (
  (direction = 'bullish' AND trend_direction = 'bullish')  -- ✅ Allow
  OR (direction = 'bearish' AND trend_direction = 'bearish')  -- ✅ Allow
  OR (direction IS NULL AND trend_direction IS NOT NULL)  -- ✅ Allow (auto direction)
)
```

**Non-Strict Mode** (`trend_strict = false`):
```sql
AND t.trend_direction IS NOT NULL  -- Just require trend exists
```

**Examples**:

| Entry Direction | Trend Direction | Strict Mode | Non-Strict Mode |
|----------------|-----------------|-------------|-----------------|
| 'bullish' | 'bullish' | ✅ Allowed | ✅ Allowed |
| 'bullish' | 'bearish' | ❌ Filtered | ✅ Allowed |
| 'bearish' | 'bearish' | ✅ Allowed | ✅ Allowed |
| 'bearish' | 'bullish' | ❌ Filtered | ✅ Allowed |
| NULL (auto) | 'bullish' | ✅ Allowed | ✅ Allowed |
| NULL (auto) | 'bearish' | ✅ Allowed | ✅ Allowed |

### Step 5: Track Price Movement (path CTE)

```sql
path AS (
  SELECT s.trading_date, s.direction, s.entry_price, s.entry_ts_ny,
         (m.timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
         m.high_price, m.low_price
  FROM setup s
  JOIN market.ohlcv_data m
    ON m.timeframe = '1m'
   AND m.timestamp >= (s.entry_ts_ny AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/Chicago'
   AND m.timestamp <= ((DATE_TRUNC('day', s.entry_ts_ny) + TIME '{{ trade_end_time }}') AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/Chicago'
   AND m.timestamp::date = s.trading_date
),
```

**What this does**:
- Only entries that passed trend filter reach this step
- Tracks 1-minute candles from entry time to trade end time
- Checks if TP or SL was hit

## Parameter Details

### `trend_enabled` (boolean)
- **Purpose**: Master switch for trend filtering
- **Default**: `false`
- **Effect**: When `false`, all trend CTEs are skipped (Jinja2 `{% if trend_enabled %}` blocks)

### `trend_timeframe` (string)
- **Purpose**: Timeframe for trend calculation
- **Values**: `'5m'`, `'15m'`, `'30m'`, `'1h'`
- **Default**: `'15m'`
- **Effect**: Determines which candles are scanned for MA calculation
- **Example**: `'15m'` = uses 15-minute candles to determine trend

### `trend_period` (integer)
- **Purpose**: Number of periods for moving average
- **Default**: `20`
- **Effect**: `ROWS BETWEEN {{ trend_period - 1 }} PRECEDING` = N-period MA
- **Example**: `20` = 20-period moving average (last 20 candles)

### `trend_type` (string)
- **Purpose**: Type of moving average
- **Values**: `'sma'` or `'ema'`
- **Default**: `'sma'`
- **Effect**: Currently both use same window function (EMA is approximated)
- **Note**: True EMA would require recursive CTE (more complex)

### `trend_strict` (boolean)
- **Purpose**: Strictness of trend filtering
- **Default**: `true`
- **Effect**:
  - `true`: Only allow trades in trend direction
  - `false`: Allow any trade if trend exists (even counter-trend)

## Performance Optimizations

1. **Year Filtering**: `trend_data` CTE filters by year range early
   ```sql
   WHERE DATE_PART('year', ...) BETWEEN {{ year_start }} AND {{ year_end }}
   ```

2. **LATERAL JOIN Optimization**: Uses `trading_date` for faster lookup
   ```sql
   WHERE tae.trading_date = DATE(e.entry_ts_ny)
   ```

3. **Conditional Rendering**: Trend CTEs only render if `trend_enabled = true`
   - When disabled, SQL is simpler and faster

4. **Early Filtering**: Trend filter reduces entries before expensive `path` CTE
   - Fewer entries = faster price tracking

## Code Locations

- **Parameter Processing**: `backend/app/services/runner.py:36-57`
- **SQL Templates**: `backend/app/sql/base_templates/*.sql.j2`
- **Template Engine**: `backend/app/services/sql_templates.py`
- **Trade Fetching**: `backend/app/services/trades.py:36-68` (same logic)

## Example Flow

**Input**:
```python
{
  "trend_enabled": True,
  "trend_timeframe": "15m",
  "trend_period": 20,
  "trend_type": "sma",
  "trend_strict": True,
  "direction": "bullish",
  "entry_time_start": "09:00:00",
  "entry_time_end": "10:00:00"
}
```

**SQL Generated**:
1. `trend_data` CTE: Calculates 20-period SMA on 15m candles
2. `trend_at_entry` CTE: Determines trend direction (bullish/bearish)
3. `entries` CTE: Finds 5m candles in 09:00-10:00 window
4. `setup` CTE: 
   - Joins entries with trend data
   - Filters: Only entries where `direction='bullish' AND trend_direction='bullish'`
5. `path` CTE: Tracks price movement for filtered entries
6. `hits` CTE: Determines TP/SL hits
7. Final aggregation: Groups results

**Result**: Only bullish entries during bullish trends are backtested.

