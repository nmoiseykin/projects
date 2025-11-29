# Testing Guide for iFVG Strategy

This guide explains how to test the iFVG Reversal strategy, including the liquidity filter enhancement.

## Table of Contents

1. [Unit Tests](#unit-tests)
2. [Integration Testing](#integration-testing)
3. [Manual Testing via Web UI](#manual-testing-via-web-ui)
4. [API Testing](#api-testing)
5. [Testing Liquidity Filter](#testing-liquidity-filter)
6. [Verifying Results](#verifying-results)

## Unit Tests

### Running Unit Tests

```bash
# From project root
cd backend
python -m pytest tests/test_ifvg_detector.py -v

# Run specific test class
python -m pytest tests/test_ifvg_detector.py::TestDetectFVGs -v

# Run specific test
python -m pytest tests/test_ifvg_detector.py::TestDetectFVGs::test_bullish_fvg_detection -v

# Run with coverage
python -m pytest tests/test_ifvg_detector.py --cov=app.services.fvg_detector --cov-report=html
```

### Test Coverage

The unit tests cover:

- **FVG Detection**:
  - Bullish FVG detection (`low[i] > high[i-2]`)
  - Bearish FVG detection (`high[i] < low[i-2]`)
  - Multiple FVGs
  - Edge cases (insufficient candles, no FVGs)

- **Inversion Detection**:
  - Bullish FVG inversion (bearish candle closes below gap_low)
  - Bearish FVG inversion (bullish candle closes above gap_high)
  - Timeout scenarios (inversion outside wait window)
  - No inversion within wait window

- **RR Calculation**:
  - Fixed RR mode (bullish and bearish)
  - Adaptive RR mode (bullish and bearish)
  - Correct SL/TP calculations

- **Swing Detection**:
  - Swing high detection
  - Swing low detection
  - Insufficient candles handling

- **Liquidity Matching**:
  - Bullish FVG matching swing high
  - Bearish FVG matching swing low
  - Tolerance checks
  - Time window checks
  - Wrong swing type rejection

## Integration Testing

### Prerequisites

1. **Start Services**:
   ```bash
   ./start.sh
   ```

2. **Verify Services Running**:
   ```bash
   ./test-connectivity.sh
   ```

3. **Check Database**:
   - Ensure `market.ohlcv_data` has data for your test year range
   - Verify timeframes exist (1m, 5m, 15m, 30m, 1h, 4h, 1d)

### Test Scenarios

#### Scenario 1: Basic iFVG Test (No Liquidity Filter)

**Purpose**: Verify basic FVG detection and inversion logic works.

**Steps**:
1. Navigate to `http://localhost:3000/strategies/ifvg`
2. Configure:
   - FVG Timeframe: `5m`
   - Entry Timeframe: `1m`
   - Wait Candles: `24`
   - Use Adaptive RR: `Yes`
   - Extra Margin: `5.0`
   - RR Multiple: `2.0`
   - Cutoff Time: `15:00:00`
   - Year Start: `2024`
   - Year End: `2024`
   - Liquidity Filter: `Disabled`
3. Click "Run iFVG Backtest"
4. Wait for completion
5. Verify results show:
   - Total trades > 0
   - Wins + Losses + Timeouts = Total trades
   - Win rate calculated correctly

**Expected Results**:
- Backtest completes successfully
- Results displayed in grouped format
- Metrics are reasonable (win rate 30-70% typical)

#### Scenario 2: Liquidity Filter Test

**Purpose**: Verify liquidity filter reduces trade count and improves quality.

**Steps**:
1. Run Scenario 1 first (baseline)
2. Note the number of trades
3. Run again with:
   - Liquidity Filter: `Enabled`
   - Liquidity Timeframe: `1h`
   - Swing Lookback: `5`
   - Tolerance Points: `5.0`
4. Compare results

**Expected Results**:
- Fewer trades than baseline (filtering out noise FVGs)
- Higher or similar win rate (better quality setups)
- Results show only FVGs at swing levels

#### Scenario 3: Different Liquidity Timeframes

**Purpose**: Test different liquidity timeframe options.

**Steps**:
1. Run 4 separate tests with:
   - Liquidity Timeframe: `15m`
   - Liquidity Timeframe: `30m`
   - Liquidity Timeframe: `1h`
   - Liquidity Timeframe: `4h`
2. Compare trade counts and win rates

**Expected Results**:
- Higher timeframes (1h, 4h) = fewer trades, potentially higher win rate
- Lower timeframes (15m, 30m) = more trades, potentially lower win rate
- All should complete successfully

#### Scenario 4: Tolerance Points Sensitivity

**Purpose**: Test how tolerance affects filtering.

**Steps**:
1. Run with Tolerance Points: `1.0` (strict)
2. Run with Tolerance Points: `5.0` (default)
3. Run with Tolerance Points: `10.0` (loose)
4. Compare results

**Expected Results**:
- Stricter tolerance = fewer trades
- Looser tolerance = more trades
- Win rate may vary

## Manual Testing via Web UI

### Step-by-Step Guide

1. **Access iFVG Page**:
   ```
   http://localhost:3000/strategies/ifvg
   ```

2. **Configure Parameters**:
   - Fill in all required fields
   - Enable/disable liquidity filter as needed
   - Set appropriate year range (start with 1 year for faster testing)

3. **Run Backtest**:
   - Click "Run iFVG Backtest"
   - Monitor status in "Recent Runs" section
   - Wait for status to change to "completed"

4. **View Results**:
   - Click on the run in "Recent Runs"
   - Or navigate to `/results/{run_id}?group=1`
   - Review grouped results table
   - Check metrics: trades, wins, losses, win rate, etc.

5. **Export Results** (if needed):
   - Click "Export CSV" button
   - Verify CSV contains expected columns

### UI Validation Checklist

- [ ] All input fields accept valid values
- [ ] Invalid inputs show appropriate errors
- [ ] Liquidity filter controls appear when enabled
- [ ] Liquidity filter controls hide when disabled
- [ ] Run button is disabled during execution
- [ ] Status updates in real-time
- [ ] Results display correctly
- [ ] CSV export works

## API Testing

### Using curl

#### Create iFVG Backtest (No Liquidity Filter)

```bash
curl -X POST http://localhost:8000/api/ifvg/backtests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: dev-key-change-in-production" \
  -d '{
    "scenarios": [{
      "fvg_timeframe": "5m",
      "entry_timeframe": "1m",
      "wait_candles": 24,
      "use_adaptive_rr": true,
      "extra_margin_pts": 5.0,
      "rr_multiple": 2.0,
      "cutoff_time": "15:00:00",
      "year_start": 2024,
      "year_end": 2024
    }],
    "strategy_text": "Test iFVG Strategy",
    "mode": "ifvg"
  }'
```

#### Create iFVG Backtest (With Liquidity Filter)

```bash
curl -X POST http://localhost:8000/api/ifvg/backtests \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: dev-key-change-in-production" \
  -d '{
    "scenarios": [{
      "fvg_timeframe": "5m",
      "entry_timeframe": "1m",
      "wait_candles": 24,
      "use_adaptive_rr": true,
      "extra_margin_pts": 5.0,
      "rr_multiple": 2.0,
      "cutoff_time": "15:00:00",
      "year_start": 2024,
      "year_end": 2024,
      "liquidity_enabled": true,
      "liquidity_timeframe": "1h",
      "swing_lookback": 5,
      "tolerance_pts": 5.0
    }],
    "strategy_text": "Test iFVG Strategy with Liquidity Filter",
    "mode": "ifvg"
  }'
```

#### Check Status

```bash
RUN_ID="your-run-id-here"

curl -X GET "http://localhost:8000/api/ifvg/backtests/${RUN_ID}/status" \
  -H "X-API-KEY: dev-key-change-in-production"
```

#### Get Results

```bash
curl -X GET "http://localhost:8000/api/ifvg/backtests/${RUN_ID}/results" \
  -H "X-API-KEY: dev-key-change-in-production"
```

### Using Python

```python
import requests

API_BASE = "http://localhost:8000/api"
API_KEY = "dev-key-change-in-production"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

# Create backtest
response = requests.post(
    f"{API_BASE}/ifvg/backtests",
    headers=HEADERS,
    json={
        "scenarios": [{
            "fvg_timeframe": "5m",
            "entry_timeframe": "1m",
            "wait_candles": 24,
            "use_adaptive_rr": True,
            "extra_margin_pts": 5.0,
            "rr_multiple": 2.0,
            "cutoff_time": "15:00:00",
            "year_start": 2024,
            "year_end": 2024,
            "liquidity_enabled": True,
            "liquidity_timeframe": "1h",
            "swing_lookback": 5,
            "tolerance_pts": 5.0
        }],
        "strategy_text": "Python API Test",
        "mode": "ifvg"
    }
)

run_id = response.json()["run_id"]
print(f"Created run: {run_id}")

# Check status
status_response = requests.get(
    f"{API_BASE}/ifvg/backtests/{run_id}/status",
    headers=HEADERS
)
print(f"Status: {status_response.json()}")

# Get results (after completion)
results_response = requests.get(
    f"{API_BASE}/ifvg/backtests/{run_id}/results",
    headers=HEADERS
)
print(f"Results: {results_response.json()}")
```

## Testing Liquidity Filter

### Verification Steps

1. **Check Logs**:
   ```bash
   docker logs -f project-forge_api_1 | grep -i "liquidity\|swing\|fvg"
   ```

   Look for:
   - "Applying liquidity filter: timeframe=..."
   - "Detected X swing points on ... timeframe"
   - "Liquidity filter: X FVGs -> Y FVGs at liquidity levels"

2. **Compare Trade Counts**:
   - Run same scenario with and without liquidity filter
   - Liquidity filter should reduce trade count
   - Win rate should be similar or better

3. **Verify Swing Detection**:
   - Use a known date/time with clear swing levels
   - Check if FVGs at those levels are detected
   - Verify FVGs not at swing levels are filtered out

### Expected Behavior

**With Liquidity Filter Enabled**:
- Fewer total trades (only FVGs at swing levels)
- Higher average FVG size (more significant gaps)
- Potentially higher win rate (better quality setups)
- Logs show filtering activity

**With Liquidity Filter Disabled**:
- More total trades (all FVGs)
- Lower average FVG size (includes noise)
- Standard win rate
- No filtering logs

## Verifying Results

### Result Structure

Results should include:

1. **Grouping Information**:
   - `fvg_timeframe`: e.g., "5m"
   - `entry_timeframe`: e.g., "1m"
   - `year`: e.g., 2024
   - `direction`: "bullish" or "bearish"
   - `use_adaptive_rr`: true/false

2. **Totals**:
   - `total_trades`: Total number of trades
   - `wins`: Number of winning trades
   - `losses`: Number of losing trades
   - `timeouts`: Number of trades that hit cutoff time

3. **KPIs**:
   - `win_rate_percent`: Win rate percentage
   - `avg_fvg_size`: Average FVG size in points
   - `avg_tp_pts`: Average take profit points
   - `avg_sl_pts`: Average stop loss points
   - `expectancy_r`: Expectancy in R units
   - `profit_factor`: Profit factor

### Validation Checks

- [ ] `wins + losses + timeouts == total_trades`
- [ ] `win_rate_percent == (wins / total_trades) * 100`
- [ ] `avg_fvg_size > 0` (if trades exist)
- [ ] `avg_tp_pts > avg_sl_pts` (for adaptive RR with rr_multiple > 1)
- [ ] Results grouped correctly by year, direction, RR mode
- [ ] All timestamps in NY timezone
- [ ] No negative values for counts or percentages

### Common Issues

1. **No Results**:
   - Check if data exists for year range
   - Verify timeframes are available
   - Check logs for errors
   - Ensure liquidity filter isn't too strict

2. **Unexpected Trade Count**:
   - Verify FVG detection is working (check logs)
   - Check inversion detection (wait_candles may be too short)
   - Verify liquidity filter settings (if enabled)

3. **Zero Win Rate**:
   - Check if TP/SL are reasonable
   - Verify path simulation is working
   - Check if cutoff_time is too early

## Performance Testing

### Test with Different Year Ranges

1. **Small Range** (1 year):
   - Should complete in < 5 minutes
   - Good for quick testing

2. **Medium Range** (2-3 years):
   - Should complete in < 15 minutes
   - Good for validation

3. **Large Range** (5+ years):
   - May take 30+ minutes
   - Good for final validation

### Monitor Performance

```bash
# Watch API logs
docker logs -f project-forge_api_1

# Check database queries
docker exec -it project-forge_db_1 psql -U aurora_user -d aurora_db -c "
  SELECT pid, state, query_start, now() - query_start AS duration, query
  FROM pg_stat_activity
  WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
  ORDER BY duration DESC;
"
```

## Troubleshooting

### Tests Fail

1. **Import Errors**:
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install pytest pytest-cov
   ```

2. **Database Connection**:
   - Ensure database is running
   - Check connection settings in `.env`

3. **Missing Data**:
   - Verify `market.ohlcv_data` has data
   - Check year range matches available data

### Backtest Fails

1. **Check Logs**:
   ```bash
   docker logs project-forge_api_1 | tail -100
   ```

2. **Verify Parameters**:
   - All required fields filled
   - Valid year range
   - Reasonable timeframes

3. **Database Issues**:
   - Check if database is accessible
   - Verify tables exist
   - Check for connection errors

## Next Steps

After successful testing:

1. **Compare Results**:
   - Run multiple scenarios
   - Compare with/without liquidity filter
   - Document findings

2. **Optimize Parameters**:
   - Adjust tolerance_pts
   - Try different liquidity timeframes
   - Fine-tune swing_lookback

3. **Production Readiness**:
   - Test with full year ranges
   - Verify performance is acceptable
   - Document any limitations

