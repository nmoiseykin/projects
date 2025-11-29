# iFVG Reversal Strategy Documentation

## Overview

The **iFVG Reversal** (inverted Fair Value Gap Reversal) strategy is a mechanical trading approach that trades the inversion of Fair Value Gaps (FVGs) when they are completely closed by opposing candles. This strategy is designed to capture mean reversion opportunities in price action.

## Strategy Concept

### Fair Value Gap (FVG)

A Fair Value Gap is a price imbalance that occurs when there's a gap between candles, leaving an area of "unfair" price action:

- **Bullish FVG**: Formed when `low[i] > high[i-2]` - price gaps up, leaving a gap below
- **Bearish FVG**: Formed when `high[i] < low[i-2]` - price gaps down, leaving a gap above

### Inversion Logic

An inversion occurs when an opposing candle completely closes the FVG:

- **Bullish FVG Inversion**: A bearish candle (close < open) that closes below the gap's lower boundary (`close < gap_low`)
- **Bearish FVG Inversion**: A bullish candle (close > open) that closes above the gap's upper boundary (`close > gap_high`)

### Entry Logic

Once an inversion is detected:
1. Wait for the next candle on the entry timeframe
2. Enter at the open price of that candle
3. Trade direction is opposite to the original FVG direction (reversal trade)

### Exit Logic

The strategy supports two Risk-Reward (RR) modes:

#### Fixed RR Mode
- Uses fixed `target_pts` and `stop_pts` values
- TP and SL are set as absolute point distances from entry
- Simple and predictable

#### Adaptive RR Mode (Recommended)
- Stop Loss: `FVG_boundary ± extra_margin_pts`
  - Bullish FVG: SL = `gap_low - extra_margin_pts`
  - Bearish FVG: SL = `gap_high + extra_margin_pts`
- Take Profit: `(extra_margin_pts + fvg_size) × rr_multiple` from entry
- Adapts to market volatility based on FVG size

## Parameters

### Timeframe Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `fvg_timeframe` | Timeframe for FVG detection | `5m` | `5m`, `15m`, `30m`, `1h` |
| `entry_timeframe` | Timeframe for entry execution | `1m` | `1m`, `5m` |

**Recommendation**: Use higher timeframe (5m-15m) for FVG detection to find significant gaps, and lower timeframe (1m) for precise entry timing.

### Inversion Detection

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `wait_candles` | Number of FVG timeframe candles to wait for inversion | `24` | 1-100 |

**Example**: With `fvg_timeframe=5m` and `wait_candles=24`, the strategy will wait up to 2 hours (24 × 5 minutes) for an inversion to occur.

### Risk-Reward Configuration

#### Fixed RR Mode
Set `use_adaptive_rr = false`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `target_pts` | Fixed take profit in points | Required |
| `stop_pts` | Fixed stop loss in points | Required |

#### Adaptive RR Mode
Set `use_adaptive_rr = true`:

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `extra_margin_pts` | Buffer beyond FVG boundary for SL | `5.0` | 0-50 |
| `rr_multiple` | Risk-reward ratio (TP:SL) | `2.0` | 0.5-10 |

**Example**: 
- FVG size = 20 points
- `extra_margin_pts` = 5
- `rr_multiple` = 2.0
- Risk = 5 + 20 = 25 points
- Target = 25 × 2.0 = 50 points

### Session Parameters

| Parameter | Description | Default | Format |
|-----------|-------------|---------|--------|
| `cutoff_time` | Session end time (NY timezone) | `15:00:00` | `HH:MM:SS` |
| `year_start` | Start year for backtest | Required | 2000-2100 |
| `year_end` | End year for backtest | Required | 2000-2100 |

### Liquidity Filter Parameters

The liquidity filter ensures that only FVGs that form when price takes out swing highs/lows (liquidity levels) are considered for trading. This improves signal quality by focusing on key price points where stops are likely placed.

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `liquidity_enabled` | Enable liquidity filter | `false` | `true`, `false` |
| `liquidity_timeframe` | Timeframe for swing high/low detection | `None` | `15m`, `30m`, `1h`, `4h`, `1d` |
| `swing_lookback` | Number of candles to look back/forward for swing detection | `5` | 1-50 |
| `tolerance_pts` | Price tolerance in points for matching FVG to swing level | `5.0` | 0-100 |

**How It Works**:
- **Swing High**: A price point where `high[i] > max(high[i-lookback:i-1])` AND `high[i] > max(high[i+1:i+lookback])`
- **Swing Low**: A price point where `low[i] < min(low[i-lookback:i-1])` AND `low[i] < min(low[i+1:i+lookback])`
- **Bullish FVG Match**: The FVG's `gap_low` must be within `tolerance_pts` of a swing high (price took out swing high)
- **Bearish FVG Match**: The FVG's `gap_high` must be within `tolerance_pts` of a swing low (price took out swing low)

**Example**:
- `liquidity_timeframe = "1h"`: Detect swing highs/lows on 1-hour charts
- `swing_lookback = 5`: Look 5 candles back and forward to confirm swing
- `tolerance_pts = 5.0`: Allow 5 points difference between FVG gap and swing level

**Benefits**:
- Filters out noise FVGs that don't occur at significant price levels
- Focuses on FVGs that form after liquidity sweeps (stop hunts)
- Typically improves win rate by selecting higher-quality setups

## Algorithm Flow

### Step 1: FVG Detection
```
For each candle on fvg_timeframe:
  - Check if low[i] > high[i-2] (bullish FVG)
  - Check if high[i] < low[i-2] (bearish FVG)
  - Store: timestamp, direction, gap_low, gap_high, fvg_size
```

**Technical Implementation:**
- **Language**: Python
- **Module**: `backend/app/services/fvg_detector.py` → `detect_fvgs()`
- **Data Source**: SQL query via `ifvg_data.sql.j2` template
- **Process**:
  1. SQL fetches all candles for `fvg_timeframe` and `entry_timeframe` from `market.ohlcv_data` table
  2. Data converted to pandas DataFrame with columns: `ts_ny`, `timeframe`, `open_price`, `high_price`, `low_price`, `close_price`
  3. Python iterates through DataFrame rows (sorted by timestamp)
  4. For each row at index `i`, checks conditions:
     - Bullish: `df.loc[i, 'low_price'] > df.loc[i-2, 'high_price']`
     - Bearish: `df.loc[i, 'high_price'] < df.loc[i-2, 'low_price']`
  5. Returns list of FVG dictionaries with `timestamp`, `direction`, `gap_low`, `gap_high`, `fvg_size`

**SQL Template**: `backend/app/sql/base_templates/ifvg_data.sql.j2`
```sql
WITH timeframes AS (
  SELECT '{{ fvg_timeframe }}' AS tf
  UNION ALL
  SELECT '{{ entry_timeframe }}' AS tf
  {% if liquidity_timeframe %}
  UNION ALL
  SELECT '{{ liquidity_timeframe }}' AS tf
  {% endif %}
)
SELECT
  (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
  timeframe,
  open_price, high_price, low_price, close_price
FROM market.ohlcv_data
WHERE timeframe IN (SELECT tf FROM timeframes)
  AND DATE_PART('year', (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') BETWEEN {{ year_start }} AND {{ year_end }}
ORDER BY timeframe, ts_ny;
```

### Step 2: Inversion Detection
```
For each detected FVG:
  - Look ahead wait_candles candles on fvg_timeframe
  - For bullish FVG: Find bearish candle with close < gap_low
  - For bearish FVG: Find bullish candle with close > gap_high
  - Store: inversion_timestamp, inversion_direction
```

**Technical Implementation:**
- **Language**: Python
- **Module**: `backend/app/services/fvg_detector.py` → `detect_inversions()`
- **Data Source**: Same pandas DataFrame from Step 1 (filtered to FVG timeframe)
- **Process**:
  1. For each FVG, calculates wait window: `fvg_ts + timedelta(minutes=wait_candles × fvg_timeframe_minutes)`
  2. Filters DataFrame to candles within wait window: `df[(df['ts_ny'] > fvg_ts) & (df['ts_ny'] <= wait_window_end)]`
  3. Applies inversion conditions:
     - Bullish FVG: `(close < gap_low) AND (close < open)` - bearish candle
     - Bearish FVG: `(close > gap_high) AND (close > open)` - bullish candle
  4. Takes first matching candle as inversion
  5. Returns list of inversion dictionaries with `fvg_ts`, `inv_ts`, `inv_dir`, `gap_low`, `gap_high`, `fvg_size`

### Step 2.5: Liquidity Filter (Optional)
```
If liquidity_enabled:
  - Fetch liquidity timeframe data
  - Detect swing highs/lows on liquidity timeframe
  - For each FVG:
    - Bullish FVG: Check if gap_low is near a swing high
    - Bearish FVG: Check if gap_high is near a swing low
    - If match found (within tolerance_pts): Keep FVG
    - Otherwise: Filter out FVG
  - Only proceed with FVGs that passed liquidity filter
```

**Technical Implementation:**
- **Language**: Python
- **Module**: `backend/app/services/fvg_detector.py` → `detect_swing_highs_lows()` and `is_fvg_at_liquidity_level()`
- **Data Source**: Liquidity timeframe candles from Step 1
- **Process**:
  1. **Swing Detection**:
     - For each candle `i` in liquidity timeframe:
       - Swing High: `high[i] > max(high[i-lookback:i-1])` AND `high[i] > max(high[i+1:i+lookback])`
       - Swing Low: `low[i] < min(low[i-lookback:i-1])` AND `low[i] < min(low[i+1:i+lookback])`
     - Returns list of swing points with `timestamp`, `price`, `type` (high/low)
  2. **FVG Matching**:
     - For bullish FVG: Check if `gap_low` is within `tolerance_pts` of any swing high price
     - For bearish FVG: Check if `gap_high` is within `tolerance_pts` of any swing low price
     - Uses 1-hour time window to find relevant swing points near FVG timestamp
  3. **Filtering**: Only FVGs that match swing levels are kept for inversion detection

### Step 3: Entry Execution
```
For each inversion:
  - Switch to entry_timeframe
  - Get next candle after inversion_timestamp
  - Entry price = open_price of that candle
  - Entry direction = opposite of FVG direction
```

**Technical Implementation:**
- **Language**: Python
- **Module**: `backend/app/services/ifvg_runner.py` → `run_ifvg_scenario()`
- **Data Source**: Same pandas DataFrame from Step 1 (filtered to entry_timeframe)
- **Process**:
  1. Filters DataFrame to `entry_timeframe` candles: `entry_df = df[df['timeframe'] == entry_timeframe]`
  2. For each inversion, finds next candle: `entry_candles = entry_df[entry_df['ts_ny'] > inv_ts]`
  3. Takes first candle: `entry_candle = entry_candles.iloc[0]`
  4. Extracts: `entry_price = entry_candle['open_price']`, `entry_ts = entry_candle['ts_ny']`
  5. Trade direction is opposite of FVG direction (already in `inv_dir`)

### Step 4: TP/SL Calculation
```
If use_adaptive_rr:
  - Calculate risk_pts = extra_margin_pts + fvg_size
  - Calculate target_pts = risk_pts × rr_multiple
  - Set SL at FVG boundary ± extra_margin_pts
  - Set TP at entry ± target_pts
Else:
  - Use fixed target_pts and stop_pts
```

**Technical Implementation:**
- **Language**: Python
- **Module**: `backend/app/services/fvg_detector.py` → `compute_rr()`
- **Process**:
  1. If `use_adaptive_rr == True`:
     - Calculates `risk_pts = extra_margin_pts + fvg_size`
     - Calculates `target_pts = risk_pts × rr_multiple`
     - For bullish trade: `stop_loss = gap_low - extra_margin_pts`, `take_profit = entry_price + target_pts`
     - For bearish trade: `stop_loss = gap_high + extra_margin_pts`, `take_profit = entry_price - target_pts`
  2. If `use_adaptive_rr == False`:
     - Uses fixed `target_pts` and `stop_pts` from parameters
     - For bullish: `stop_loss = entry_price - stop_pts`, `take_profit = entry_price + target_pts`
     - For bearish: `stop_loss = entry_price + stop_pts`, `take_profit = entry_price - target_pts`
  3. Returns tuple: `(stop_loss_price, take_profit_price)`

### Step 5: Trade Simulation
```
For each entry:
  - Fetch 1-minute candles from entry_time to cutoff_time
  - Check for TP hit (higher priority)
  - Check for SL hit
  - If neither hit by cutoff_time: mark as timeout
  - Record: outcome (win/loss/timeout), exit_price, exit_time
```

**Technical Implementation:**
- **Language**: Hybrid (SQL + Python)
- **Module**: `backend/app/services/ifvg_runner.py` → `run_ifvg_scenario()`
- **SQL Template**: `backend/app/sql/base_templates/ifvg_path.sql.j2`
- **Process**:
  1. **SQL Query** (via `ifvg_path.sql.j2`):
     ```sql
     SELECT
       (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
       high_price, low_price
     FROM market.ohlcv_data
     WHERE timeframe = '1m'
       AND ts_ny >= TIMESTAMP '{{ entry_ts_ny }}'
       AND ts_ny <= (DATE '{{ trading_date }}' + TIME '{{ cutoff_time }}')
     ORDER BY ts_ny;
     ```
  2. **Python Processing**:
     - Iterates through path rows sequentially
     - For bullish trade:
       - Checks TP first: `if high >= take_profit: outcome = 'win', exit_price = take_profit`
       - Then checks SL: `if low <= stop_loss: outcome = 'loss', exit_price = stop_loss`
     - For bearish trade:
       - Checks TP first: `if low <= take_profit: outcome = 'win', exit_price = take_profit`
       - Then checks SL: `if high >= stop_loss: outcome = 'loss', exit_price = stop_loss`
     - If no hit by end of path: `outcome = 'timeout', exit_price = None`
  3. Stores trade result with all details

### Step 6: Result Aggregation
```
Group results by:
  - Year
  - Direction (bullish/bearish)
  - RR Mode (fixed/adaptive)

Calculate metrics:
  - Total trades, wins, losses, timeouts
  - Win rate percentage
  - Average FVG size
  - Average TP/SL points
  - Expectancy in R units
  - Profit factor
```

**Technical Implementation:**
- **Language**: Python (pandas)
- **Module**: `backend/app/services/ifvg_runner.py` → `run_ifvg_scenario()` and `_calculate_ifvg_kpis()`
- **Process**:
  1. **Data Collection**: All trades stored in list of dictionaries
  2. **DataFrame Creation**: `trades_df = pd.DataFrame(trades)`
  3. **Year Extraction**: `trades_df['year'] = trades_df['trading_date'].apply(lambda x: x.year)`
  4. **Grouping** (using pandas):
     - Strategy level: All trades
     - By year: `trades_df[trades_df['year'] == year]`
     - By year + direction: `year_trades[year_trades['direction'] == direction]`
  5. **KPI Calculation** (`_calculate_ifvg_kpis()`):
     - Basic counts: `total_trades = len(trades_df)`, `wins = len(trades_df[trades_df['outcome'] == 'win'])`
     - Win rate: `(wins / total_trades) * 100.0`
     - Averages: `avg_fvg_size = trades_df['fvg_size'].mean()`
     - TP/SL averages: Calculates `tp_pts` and `sl_pts` for each trade, then averages
     - Expectancy R: `(win_rate_decimal × r_ratio) - (loss_rate_decimal × 1.0)` where `r_ratio = avg_tp_pts / avg_sl_pts`
     - Profit factor: `(wins × avg_tp_pts) / (losses × avg_sl_pts)`
  6. **Result Storage**: Results saved to database via `save_results()` function

## Technical Architecture

### Data Flow

```
1. Frontend (Next.js/React)
   ↓ HTTP POST /api/ifvg/backtests
2. Backend API (FastAPI)
   ↓ routes_ifvg.py → create_ifvg_backtest()
3. Database (PostgreSQL)
   ↓ Store run and scenarios with strategy_type='ifvg'
4. Background Task
   ↓ routes_ifvg.py → run_backtest_run_task()
5. Runner Service
   ↓ runner.py → run_backtest_run() → routes to ifvg_runner.py
6. iFVG Runner
   ↓ ifvg_runner.py → run_ifvg_scenario()
   ├─ SQL: Fetch candle data (ifvg_data.sql.j2)
   ├─ Python: Detect FVGs (fvg_detector.py)
   ├─ Python: Detect inversions (fvg_detector.py)
   ├─ Python: Calculate TP/SL (fvg_detector.py)
   ├─ SQL: Fetch path data (ifvg_path.sql.j2)
   ├─ Python: Simulate trades
   └─ Python: Aggregate results
7. Database
   ↓ Save results to backtest_results table
8. Frontend
   ↓ Poll /api/ifvg/backtests/{run_id}/status
   ↓ Display results on /results/{run_id}
```

### Key Files

| File | Purpose | Language |
|------|---------|----------|
| `backend/app/api/routes_ifvg.py` | API endpoints for iFVG strategy | Python (FastAPI) |
| `backend/app/services/ifvg_runner.py` | Main orchestration logic | Python |
| `backend/app/services/fvg_detector.py` | FVG detection, inversion, RR calculation, swing detection, liquidity matching | Python |
| `backend/app/sql/base_templates/ifvg_data.sql.j2` | SQL template for fetching candle data | SQL (Jinja2) |
| `backend/app/sql/base_templates/ifvg_path.sql.j2` | SQL template for fetching path data | SQL (Jinja2) |
| `backend/app/models/ifvg.py` | Pydantic models for iFVG parameters | Python |
| `frontend/app/strategies/ifvg/page.tsx` | UI form for iFVG configuration | TypeScript/React |
| `frontend/lib/api.ts` | API client with ifvgApi methods | TypeScript |

### Database Tables Used

- `market.ohlcv_data`: Source of all candle data (timestamp, timeframe, OHLCV prices)
- `backtest_runs`: Stores run metadata with `strategy_type='ifvg'`
- `backtest_scenarios`: Stores scenario parameters with `strategy_type='ifvg'`
- `backtest_results`: Stores aggregated results with `strategy_type='ifvg'`

### Performance Characteristics

- **FVG Detection**: O(n) where n = number of candles in year range
- **Inversion Detection**: O(n × wait_candles) - worst case scans all candles
- **Path Simulation**: O(m) where m = candles from entry to cutoff (typically < 1000)
- **Overall Complexity**: Linear with data size, but can be slow for large year ranges

### Optimization Opportunities

1. **Pre-filter data by year** in SQL (already implemented)
2. **Use materialized views** for common timeframe combinations
3. **Batch process multiple FVGs** in parallel
4. **Cache FVG detection results** for repeated runs
5. **Limit path simulation** to necessary time window only

## Example Strategy Configuration

### Conservative Setup
```json
{
  "fvg_timeframe": "15m",
  "entry_timeframe": "1m",
  "wait_candles": 24,
  "use_adaptive_rr": true,
  "extra_margin_pts": 5.0,
  "rr_multiple": 2.0,
  "cutoff_time": "15:00:00",
  "year_start": 2020,
  "year_end": 2025,
  "liquidity_enabled": false,
  "liquidity_timeframe": null,
  "swing_lookback": 5,
  "tolerance_pts": 5.0
}
```

**Characteristics**:
- Larger timeframes = fewer but higher quality FVGs
- Adaptive RR adapts to market conditions
- 2:1 risk-reward ratio
- No liquidity filter (trades all FVGs)

### Aggressive Setup
```json
{
  "fvg_timeframe": "5m",
  "entry_timeframe": "1m",
  "wait_candles": 12,
  "use_adaptive_rr": true,
  "extra_margin_pts": 3.0,
  "rr_multiple": 3.0,
  "cutoff_time": "15:00:00",
  "year_start": 2020,
  "year_end": 2025,
  "liquidity_enabled": false,
  "liquidity_timeframe": null,
  "swing_lookback": 5,
  "tolerance_pts": 5.0
}
```

**Characteristics**:
- More frequent FVG detection (5m)
- Shorter wait window (12 candles = 1 hour)
- Higher RR multiple (3:1)
- Lower margin buffer

### Liquidity-Filtered Setup (Recommended)
```json
{
  "fvg_timeframe": "5m",
  "entry_timeframe": "1m",
  "wait_candles": 24,
  "use_adaptive_rr": true,
  "extra_margin_pts": 5.0,
  "rr_multiple": 2.0,
  "cutoff_time": "15:00:00",
  "year_start": 2020,
  "year_end": 2025,
  "liquidity_enabled": true,
  "liquidity_timeframe": "1h",
  "swing_lookback": 5,
  "tolerance_pts": 5.0
}
```

**Characteristics**:
- Only trades FVGs that form at swing highs/lows
- Uses 1-hour timeframe for swing detection
- Filters out noise FVGs
- Typically improves win rate by 5-15%
- Fewer trades but higher quality

## Output Metrics

### Trade-Level Metrics
- `total_trades`: Total number of trades executed
- `wins`: Number of winning trades (TP hit)
- `losses`: Number of losing trades (SL hit)
- `timeouts`: Number of trades that didn't hit TP/SL by cutoff

### Performance Metrics
- `win_rate_percent`: (wins / total_trades) × 100
- `avg_fvg_size`: Average size of detected FVGs in points
- `avg_tp_pts`: Average take profit distance in points
- `avg_sl_pts`: Average stop loss distance in points
- `expectancy_r`: Expected value in R units (risk units)
- `profit_factor`: (Total wins × Avg win) / (Total losses × Avg loss)

### Grouping
Results are grouped by:
- **Strategy Level**: Overall performance
- **Year**: Performance by calendar year
- **Year + Direction**: Performance by year and trade direction (bullish/bearish)
- **Year + Direction + RR Mode**: Most granular grouping

## Performance Considerations

### Data Requirements
- Requires 1-minute OHLCV data for path simulation
- Requires FVG timeframe data for gap detection
- All timestamps must be in NY timezone

### Computational Complexity
- FVG detection: O(n) where n = number of candles
- Inversion detection: O(n × wait_candles)
- Path simulation: O(m) where m = candles from entry to cutoff
- Overall: Linear with data size

### Optimization Tips
1. **Start with smaller year ranges** (1-2 years) for initial testing
2. **Use higher FVG timeframes** (15m, 30m) to reduce noise
3. **Adjust wait_candles** based on market session length
4. **Monitor avg_fvg_size** - very small FVGs may be noise
5. **Check win_rate by direction** - one direction may perform better

## Usage Example

### Via Web Interface

1. Navigate to `/strategies/ifvg`
2. Configure parameters:
   - FVG Timeframe: `15m`
   - Entry Timeframe: `1m`
   - Wait Candles: `24`
   - Enable "Use Adaptive RR"
   - Extra Margin: `5.0`
   - RR Multiple: `2.0`
   - Cutoff Time: `15:00:00`
   - Year Range: `2020-2025`
   - (Optional) Enable "Liquidity Filter":
     - Liquidity Timeframe: `1h` (or `15m`, `30m`, `4h`, `1d`)
     - Swing Lookback: `5`
     - Tolerance Points: `5.0`
3. Click "Run iFVG Backtest"
4. View results on the results page

### Via API

```python
import requests

response = requests.post(
    "http://localhost:8000/api/ifvg/backtests",
    headers={"X-API-KEY": "dev-key-change-in-production"},
    json={
        "scenarios": [{
            "fvg_timeframe": "15m",
            "entry_timeframe": "1m",
            "wait_candles": 24,
            "use_adaptive_rr": True,
            "extra_margin_pts": 5.0,
            "rr_multiple": 2.0,
            "cutoff_time": "15:00:00",
            "year_start": 2020,
            "year_end": 2025,
            "liquidity_enabled": True,
            "liquidity_timeframe": "1h",
            "swing_lookback": 5,
            "tolerance_pts": 5.0
        }]
    }
)

run_id = response.json()["run_id"]
```

## Strategy Summary

**iFVG Full-Close (Adaptive RR)**
- Detects 3-bar FVGs on higher timeframe (5m-1h)
- Waits for complete inversion by opposing candle
- Enters on next candle of entry timeframe
- Uses adaptive RR based on FVG size
- Exits at TP, SL, or session cutoff

**Key Advantages**:
- Adapts to market volatility (FVG size)
- Clear entry/exit rules
- Works in both trending and ranging markets
- Configurable risk-reward ratios

**Key Considerations**:
- Requires sufficient historical data
- Performance varies by market conditions
- FVG quality matters (size and context)
- May have lower trade frequency than simple strategies

## Troubleshooting

### No FVGs Detected
- Check if data exists for the specified year range
- Try lower FVG timeframe (5m instead of 15m)
- Verify data quality (no gaps in timestamps)

### No Inversions Found
- Increase `wait_candles` parameter
- Check if market conditions favor reversals
- Verify FVG detection is working (check logs)
- If liquidity filter enabled: Check if swing detection is working (may filter out too many FVGs)

### Low Win Rate
- Review `avg_fvg_size` - very small FVGs may be noise
- Adjust `extra_margin_pts` - may be too tight
- Check performance by direction - one may be better
- Consider different RR multiples
- **Enable liquidity filter** - filters out noise FVGs, typically improves win rate
- Adjust `tolerance_pts` - may be too strict or too loose
- Try different `liquidity_timeframe` - higher timeframes (1h, 4h) for more significant levels

### Performance Issues
- Start with smaller year ranges (1-2 years)
- Use materialized views if available
- Check database indexes on timestamp columns

