#!/bin/bash
# Reset a stuck backtest run

RUN_ID="${1:-a8325201-3e06-4106-98bd-8792c1338704}"

echo "🔄 Resetting stuck backtest run: $RUN_ID"
echo ""

cd ~/projects/project-forge

PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db << EOF
-- Reset the stuck run
UPDATE backtest_runs 
SET 
    status = 'failed',
    finished_at = NOW()
WHERE id = '$RUN_ID'::uuid;

-- Reset all scenarios for this run
UPDATE backtest_scenarios 
SET 
    status = 'failed',
    error = 'Run was manually reset due to transaction error'
WHERE run_id = '$RUN_ID'::uuid
  AND status IN ('running', 'pending');

-- Show the updated status
SELECT 
    id,
    status,
    total_scenarios,
    completed_scenarios,
    created_at,
    started_at,
    finished_at
FROM backtest_runs 
WHERE id = '$RUN_ID'::uuid;

-- Show scenario statuses
SELECT 
    status,
    COUNT(*) as count
FROM backtest_scenarios 
WHERE run_id = '$RUN_ID'::uuid
GROUP BY status;
EOF

echo ""
echo "✅ Run $RUN_ID has been reset to 'failed' status"
echo ""
echo "You can now create a new backtest run."


