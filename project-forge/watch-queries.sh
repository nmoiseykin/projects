#!/bin/bash
# Watch running SQL queries in real-time (updates every 2 seconds)

cd ~/projects/project-forge

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_NAME" ]; then
    echo "❌ Database credentials not set"
    exit 1
fi

INTERVAL=${1:-2}  # Default 2 seconds

echo "🔍 Watching SQL queries (updating every ${INTERVAL}s, press Ctrl+C to stop)"
echo ""

while true; do
    clear
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Running SQL Queries - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
SELECT 
    pid,
    state,
    EXTRACT(EPOCH FROM (NOW() - query_start))::INTEGER as duration_sec,
    LEFT(query, 80) as query_preview
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;
EOF
    
    echo ""
    echo "Press Ctrl+C to stop..."
    sleep $INTERVAL
done


