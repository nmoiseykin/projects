# Refreshing Materialized Views for Trend Following

## Overview

Materialized views pre-compute SMA values for all candles, making queries 450x faster. These views need to be refreshed periodically when new data is added.

## Creating Views (One-Time Setup)

Run the creation script:

```bash
# Connect to your database and run:
psql -h localhost -U your_user -d your_database -f backend/create_trend_views.sql
```

Or from within psql:
```sql
\i backend/create_trend_views.sql
```

This creates 5 materialized views:
- `market.sma_15m_20` - 15m timeframe, 20-period SMA
- `market.sma_15m_50` - 15m timeframe, 50-period SMA
- `market.sma_30m_20` - 30m timeframe, 20-period SMA
- `market.sma_1h_20` - 1h timeframe, 20-period SMA
- `market.sma_5m_20` - 5m timeframe, 20-period SMA

## Refreshing Views

### Manual Refresh

Refresh all views:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_15m_20;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_15m_50;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_30m_20;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_1h_20;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_5m_20;
```

**Note**: `CONCURRENTLY` allows queries to continue during refresh (recommended for production).

### Automated Refresh (Cron Job)

Create a script `refresh_trend_views.sh`:
```bash
#!/bin/bash
psql -h localhost -U your_user -d your_database <<EOF
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_15m_20;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_15m_50;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_30m_20;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_1h_20;
REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_5m_20;
EOF
```

Add to crontab (refresh daily at 2 AM):
```bash
0 2 * * * /path/to/refresh_trend_views.sh
```

## When to Refresh

- **Daily**: If you add new candle data daily
- **After bulk data imports**: After importing historical data
- **Weekly**: If data updates are infrequent

## Performance Notes

- **Initial creation**: May take 5-15 minutes depending on data size
- **Refresh**: Usually 1-5 minutes (only recalculates new/changed data)
- **Query speed**: 0.3-1.2 seconds for 6-year backtests (vs 9+ minutes before)

## Checking View Status

```sql
-- Check if views exist
SELECT schemaname, matviewname, pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size
FROM pg_matviews
WHERE schemaname = 'market' AND matviewname LIKE 'sma_%'
ORDER BY matviewname;

-- Check last refresh time (if available)
SELECT * FROM pg_stat_user_tables WHERE schemaname = 'market' AND relname LIKE 'sma_%';
```

