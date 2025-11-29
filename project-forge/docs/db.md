# Database Schema

## Expected Table: `market.ohlcv_data`

```sql
CREATE TABLE market.ohlcv_data (
    timestamp TIMESTAMP NOT NULL,  -- Stored in America/Chicago
    timeframe TEXT NOT NULL,       -- '1m', '5m', '15m', etc.
    open_price NUMERIC NOT NULL,
    high_price NUMERIC NOT NULL,
    low_price NUMERIC NOT NULL,
    close_price NUMERIC NOT NULL,
    volume NUMERIC,
    PRIMARY KEY (timestamp, timeframe)
);
```

### Recommended Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_ohlcv_tf_ts 
ON market.ohlcv_data(timeframe, timestamp);

CREATE INDEX IF NOT EXISTS idx_ohlcv_date 
ON market.ohlcv_data(DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'));
```

### Timezone Conversion

**CRITICAL:** All queries must convert timestamps:
```sql
(timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny
```

## Application Tables

### `backtest_runs`
```sql
CREATE TABLE backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
    total_scenarios INTEGER DEFAULT 0,
    completed_scenarios INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);
```

### `backtest_scenarios`
```sql
CREATE TABLE backtest_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES backtest_runs(id) ON DELETE CASCADE,
    params JSONB NOT NULL,  -- {entry_time, end_time, target_pts, stop_pts, direction, year_start, year_end}
    status TEXT NOT NULL,   -- 'pending', 'running', 'completed', 'failed'
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### `backtest_results`
```sql
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES backtest_scenarios(id) ON DELETE CASCADE,
    grouping JSONB,         -- {year, direction, candle_time, dow, etc.}
    totals JSONB,          -- {total_trades, wins, losses, timeouts}
    kpis JSONB,            -- {win_rate_percent, expectancy_r, profit_factor, etc.}
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_scenarios_run_id ON backtest_scenarios(run_id);
CREATE INDEX idx_results_scenario_id ON backtest_results(scenario_id);
CREATE INDEX idx_runs_status ON backtest_runs(status);
```



