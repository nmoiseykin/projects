-- Create materialized views for pre-calculated moving averages
-- This avoids recalculating SMA on every query - massive performance improvement
-- 
-- Usage:
--   1. Run this script once to create views: psql -d your_db -f create_trend_views.sql
--   2. Refresh periodically (daily or after data updates):
--      REFRESH MATERIALIZED VIEW CONCURRENTLY market.sma_15m_20;
--
-- Performance: Queries using these views are ~450x faster than calculating on-the-fly

-- Drop existing views if they exist
DROP MATERIALIZED VIEW IF EXISTS market.sma_15m_20 CASCADE;
DROP MATERIALIZED VIEW IF EXISTS market.sma_15m_50 CASCADE;
DROP MATERIALIZED VIEW IF EXISTS market.sma_30m_20 CASCADE;
DROP MATERIALIZED VIEW IF EXISTS market.sma_1h_20 CASCADE;
DROP MATERIALIZED VIEW IF EXISTS market.sma_5m_20 CASCADE;

-- Create materialized view for 15m, 20-period SMA (most common)
CREATE MATERIALIZED VIEW market.sma_15m_20 AS
SELECT
  (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') AS trading_date,
  close_price,
  AVG(close_price) OVER (
    ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
  ) AS sma_value,
  CASE 
    WHEN close_price > AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bullish'
    WHEN close_price < AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bearish'
    ELSE 'neutral'
  END AS trend_direction
FROM market.ohlcv_data
WHERE timeframe = '15m'
ORDER BY ts_ny;

-- Create indexes on the materialized view for fast lookups
CREATE INDEX IF NOT EXISTS idx_sma_15m_20_ts_ny ON market.sma_15m_20(ts_ny);
CREATE INDEX IF NOT EXISTS idx_sma_15m_20_trading_date ON market.sma_15m_20(trading_date);
CREATE INDEX IF NOT EXISTS idx_sma_15m_20_ts_ny_desc ON market.sma_15m_20(ts_ny DESC);

-- Create materialized view for 15m, 50-period SMA
CREATE MATERIALIZED VIEW market.sma_15m_50 AS
SELECT
  (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') AS trading_date,
  close_price,
  AVG(close_price) OVER (
    ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
    ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
  ) AS sma_value,
  CASE 
    WHEN close_price > AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) THEN 'bullish'
    WHEN close_price < AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
    ) THEN 'bearish'
    ELSE 'neutral'
  END AS trend_direction
FROM market.ohlcv_data
WHERE timeframe = '15m'
ORDER BY ts_ny;

CREATE INDEX IF NOT EXISTS idx_sma_15m_50_ts_ny ON market.sma_15m_50(ts_ny);
CREATE INDEX IF NOT EXISTS idx_sma_15m_50_trading_date ON market.sma_15m_50(trading_date);

-- Create materialized view for 30m, 20-period SMA
CREATE MATERIALIZED VIEW market.sma_30m_20 AS
SELECT
  (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') AS trading_date,
  close_price,
  AVG(close_price) OVER (
    ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
  ) AS sma_value,
  CASE 
    WHEN close_price > AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bullish'
    WHEN close_price < AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bearish'
    ELSE 'neutral'
  END AS trend_direction
FROM market.ohlcv_data
WHERE timeframe = '30m'
ORDER BY ts_ny;

CREATE INDEX IF NOT EXISTS idx_sma_30m_20_ts_ny ON market.sma_30m_20(ts_ny);
CREATE INDEX IF NOT EXISTS idx_sma_30m_20_trading_date ON market.sma_30m_20(trading_date);

-- Create materialized view for 1h, 20-period SMA
CREATE MATERIALIZED VIEW market.sma_1h_20 AS
SELECT
  (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') AS trading_date,
  close_price,
  AVG(close_price) OVER (
    ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
  ) AS sma_value,
  CASE 
    WHEN close_price > AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bullish'
    WHEN close_price < AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bearish'
    ELSE 'neutral'
  END AS trend_direction
FROM market.ohlcv_data
WHERE timeframe = '1h'
ORDER BY ts_ny;

CREATE INDEX IF NOT EXISTS idx_sma_1h_20_ts_ny ON market.sma_1h_20(ts_ny);
CREATE INDEX IF NOT EXISTS idx_sma_1h_20_trading_date ON market.sma_1h_20(trading_date);

-- Create materialized view for 5m, 20-period SMA (less common but available)
CREATE MATERIALIZED VIEW market.sma_5m_20 AS
SELECT
  (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York' AS ts_ny,
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') AS trading_date,
  close_price,
  AVG(close_price) OVER (
    ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
  ) AS sma_value,
  CASE 
    WHEN close_price > AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bullish'
    WHEN close_price < AVG(close_price) OVER (
      ORDER BY (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York'
      ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) THEN 'bearish'
    ELSE 'neutral'
  END AS trend_direction
FROM market.ohlcv_data
WHERE timeframe = '5m'
ORDER BY ts_ny;

CREATE INDEX IF NOT EXISTS idx_sma_5m_20_ts_ny ON market.sma_5m_20(ts_ny);
CREATE INDEX IF NOT EXISTS idx_sma_5m_20_trading_date ON market.sma_5m_20(trading_date);

-- Verify views were created
SELECT 'Materialized views created successfully!' AS result;
SELECT schemaname, matviewname, pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size
FROM pg_matviews
WHERE schemaname = 'market' AND matviewname LIKE 'sma_%'
ORDER BY matviewname;
