-- Migration: Add strategy_type column to existing tables
-- Run this as postgres user: psql -d your_db -f backend/migrations/add_strategy_type.sql

-- Add strategy_type column to backtest_runs
ALTER TABLE backtest_runs ADD COLUMN IF NOT EXISTS strategy_type TEXT DEFAULT 'standard';

-- Add strategy_type column to backtest_scenarios
ALTER TABLE backtest_scenarios ADD COLUMN IF NOT EXISTS strategy_type TEXT;

-- Add strategy_type column to backtest_results
ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS strategy_type TEXT;

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_runs_strategy_type ON backtest_runs(strategy_type);
CREATE INDEX IF NOT EXISTS idx_scenarios_strategy_type ON backtest_scenarios(strategy_type);
CREATE INDEX IF NOT EXISTS idx_results_strategy_type ON backtest_results(strategy_type);

-- Update existing rows to have 'standard' strategy_type
UPDATE backtest_runs SET strategy_type = 'standard' WHERE strategy_type IS NULL;
UPDATE backtest_scenarios SET strategy_type = 'standard' WHERE strategy_type IS NULL AND run_id IN (SELECT id FROM backtest_runs WHERE strategy_type = 'standard');

-- Verify
SELECT 'Migration completed successfully!' AS result;
SELECT 
    'backtest_runs' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE strategy_type = 'standard') AS standard_rows,
    COUNT(*) FILTER (WHERE strategy_type IS NULL) AS null_rows
FROM backtest_runs
UNION ALL
SELECT 
    'backtest_scenarios' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE strategy_type = 'standard') AS standard_rows,
    COUNT(*) FILTER (WHERE strategy_type IS NULL) AS null_rows
FROM backtest_scenarios;

