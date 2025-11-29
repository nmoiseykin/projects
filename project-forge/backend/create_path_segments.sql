-- Create materialized view for pre-aggregated 5-minute path segments
-- This reduces row count by ~80% and enables fast TP/SL hit detection
-- 
-- Usage:
--   1. Run this script once to create view: psql -d your_db -f create_path_segments.sql
--   2. Refresh periodically (daily or after data updates):
--      REFRESH MATERIALIZED VIEW CONCURRENTLY market.path_segments_5m;
--
-- Performance: Queries using this view are 10-20x faster than scanning raw 1m candles

-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS market.path_segments_5m CASCADE;

-- Create materialized view: aggregate 1m candles into 5m segments
-- Each segment contains: segment_start (5m boundary), seg_low (min), seg_high (max)
CREATE MATERIALIZED VIEW market.path_segments_5m AS
SELECT
  -- Round down to 5-minute boundary (NY timezone)
  -- Use: DATE_TRUNC('hour', ts) + INTERVAL '5 minutes' * FLOOR(EXTRACT(MINUTE FROM ts) / 5)
  DATE_TRUNC('hour', (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') 
    + INTERVAL '5 minutes' * FLOOR(EXTRACT(MINUTE FROM (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') / 5) AS segment_start_ny,
  -- Store original timestamp in Chicago timezone for joins (same calculation)
  DATE_TRUNC('hour', timestamp) 
    + INTERVAL '5 minutes' * FLOOR(EXTRACT(MINUTE FROM timestamp) / 5) AS segment_start_chicago,
  -- Aggregate: min low, max high for the 5-minute window
  MIN(low_price) AS seg_low,
  MAX(high_price) AS seg_high,
  -- Also store the date for fast filtering
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') AS trading_date
FROM market.ohlcv_data
WHERE timeframe = '1m'
GROUP BY 
  DATE_TRUNC('hour', (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') 
    + INTERVAL '5 minutes' * FLOOR(EXTRACT(MINUTE FROM (timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York') / 5),
  DATE_TRUNC('hour', timestamp) 
    + INTERVAL '5 minutes' * FLOOR(EXTRACT(MINUTE FROM timestamp) / 5),
  DATE((timestamp AT TIME ZONE 'America/Chicago') AT TIME ZONE 'America/New_York')
ORDER BY segment_start_ny;

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_path_segments_5m_start_ny ON market.path_segments_5m(segment_start_ny);
CREATE INDEX IF NOT EXISTS idx_path_segments_5m_start_chicago ON market.path_segments_5m(segment_start_chicago);
CREATE INDEX IF NOT EXISTS idx_path_segments_5m_trading_date ON market.path_segments_5m(trading_date);
CREATE INDEX IF NOT EXISTS idx_path_segments_5m_range ON market.path_segments_5m(segment_start_ny, seg_low, seg_high);

-- Optional: Add GiST index for range queries (advanced optimization)
-- This enables fast TP/SL hit detection using range operators
-- ALTER TABLE market.path_segments_5m ADD COLUMN price_range numrange;
-- UPDATE market.path_segments_5m SET price_range = numrange(seg_low, seg_high, '[]');
-- CREATE INDEX idx_path_range_gist ON market.path_segments_5m USING gist(price_range);

-- Verify view was created
SELECT 'Materialized view created successfully!' AS result;
SELECT 
  pg_size_pretty(pg_total_relation_size('market.path_segments_5m')) AS size,
  COUNT(*) AS row_count,
  MIN(segment_start_ny) AS earliest_segment,
  MAX(segment_start_ny) AS latest_segment
FROM market.path_segments_5m;

