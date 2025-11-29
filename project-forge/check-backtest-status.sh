#!/bin/bash
# Check backtest execution status

RUN_ID="${1:-a8325201-3e06-4106-98bd-8792c1338704}"

echo "🔍 Checking Backtest Status for: $RUN_ID"
echo ""

# Check run status
echo "📊 Run Status:"
curl -s http://localhost:8000/api/backtests/$RUN_ID -H "X-API-KEY: dev-key-change-in-production" | python3 -m json.tool 2>/dev/null || echo "Failed to get status"
echo ""

# Check database
echo "🗄️  Database Status:"
PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db << EOF
SELECT 
    status,
    total_scenarios,
    completed_scenarios,
    created_at,
    started_at,
    finished_at
FROM backtest_runs 
WHERE id = '$RUN_ID'::uuid;

SELECT 
    status,
    COUNT(*) as count
FROM backtest_scenarios 
WHERE run_id = '$RUN_ID'::uuid
GROUP BY status;

SELECT COUNT(*) as result_count
FROM backtest_results r
JOIN backtest_scenarios s ON r.scenario_id = s.id
WHERE s.run_id = '$RUN_ID'::uuid;
EOF

echo ""
echo "📝 Recent Logs:"
tail -20 ~/projects/project-forge/logs/app.log 2>/dev/null | grep -i "scenario\|backtest\|error" | tail -5 || echo "No relevant logs found"


