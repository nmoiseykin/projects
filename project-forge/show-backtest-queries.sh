#!/bin/bash
# Show SQL queries related to backtest execution

cd ~/projects/project-forge

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Backtest-Related SQL Queries"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo -e "${RED}❌ Database credentials not set${NC}"
    exit 1
fi

# Show queries that look like backtest queries
echo -e "${BLUE}📊 Active Backtest Queries${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT 
    pid,
    state,
    EXTRACT(EPOCH FROM (NOW() - query_start))::INTEGER as duration_sec,
    CASE 
        WHEN query LIKE '%ohlcv_data%' THEN 'OHLCV Data Query'
        WHEN query LIKE '%backtest%' THEN 'Backtest Query'
        WHEN query LIKE '%WITH%' THEN 'CTE Query (likely backtest)'
        WHEN query LIKE '%market.%' THEN 'Market Data Query'
        ELSE 'Other Query'
    END as query_type,
    LEFT(query, 120) as query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
  AND (
    query ILIKE '%ohlcv_data%'
    OR query ILIKE '%backtest%'
    OR query ILIKE '%market.%'
    OR query LIKE 'WITH%'
  )
ORDER BY query_start;
EOF

echo ""
echo -e "${BLUE}📈 Query Performance${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT 
    CASE 
        WHEN query LIKE '%ohlcv_data%' THEN 'OHLCV Data'
        WHEN query LIKE '%backtest%' THEN 'Backtest'
        WHEN query LIKE '%market.%' THEN 'Market Data'
        ELSE 'Other'
    END as query_category,
    COUNT(*) as query_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - query_start)))::INTEGER as avg_duration_sec,
    MAX(EXTRACT(EPOCH FROM (NOW() - query_start)))::INTEGER as max_duration_sec,
    MIN(EXTRACT(EPOCH FROM (NOW() - query_start)))::INTEGER as min_duration_sec
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
GROUP BY query_category
ORDER BY query_count DESC;
EOF

echo ""
echo -e "${BLUE}⏱️  Long Running Backtest Queries${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT 
    pid,
    state,
    EXTRACT(EPOCH FROM (NOW() - query_start))::INTEGER as duration_sec,
    ROUND(EXTRACT(EPOCH FROM (NOW() - query_start)) / 60.0, 2) as duration_min,
    LEFT(query, 200) as query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
  AND (
    query ILIKE '%ohlcv_data%'
    OR query ILIKE '%backtest%'
    OR query ILIKE '%market.%'
  )
  AND NOW() - query_start > INTERVAL '10 seconds'
ORDER BY query_start;
EOF

echo ""
echo "💡 To kill a query: SELECT pg_terminate_backend(<pid>);"
echo ""


