#!/bin/bash
# Migration script to add strategy_type column
# This must be run as postgres superuser

DB_NAME="aurora_db"

echo "Running migration to add strategy_type column..."
echo ""

# Try different connection methods
if command -v psql &> /dev/null; then
    echo "Attempting to connect to database..."
    
    # Method 1: Try as current user (if peer auth works)
    if psql -d "$DB_NAME" -c "\q" 2>/dev/null; then
        echo "✓ Connected to database"
        psql -d "$DB_NAME" <<EOF
-- Add strategy_type column to backtest_runs
ALTER TABLE backtest_runs ADD COLUMN IF NOT EXISTS strategy_type TEXT DEFAULT 'standard';

-- Add strategy_type column to backtest_scenarios
ALTER TABLE backtest_scenarios ADD COLUMN IF NOT EXISTS strategy_type TEXT;

-- Add strategy_type column to backtest_results
ALTER TABLE backtest_results ADD COLUMN IF NOT EXISTS strategy_type TEXT;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_runs_strategy_type ON backtest_runs(strategy_type);
CREATE INDEX IF NOT EXISTS idx_scenarios_strategy_type ON backtest_scenarios(strategy_type);
CREATE INDEX IF NOT EXISTS idx_results_strategy_type ON backtest_results(strategy_type);

-- Update existing rows
UPDATE backtest_runs SET strategy_type = 'standard' WHERE strategy_type IS NULL;
UPDATE backtest_scenarios SET strategy_type = 'standard' 
WHERE strategy_type IS NULL 
AND run_id IN (SELECT id FROM backtest_runs WHERE strategy_type = 'standard');

-- Verify
SELECT 'Migration completed!' AS result;
SELECT 
    'backtest_runs' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE strategy_type = 'standard') AS standard_rows
FROM backtest_runs;
EOF
        if [ $? -eq 0 ]; then
            echo ""
            echo "✓ Migration completed successfully!"
            exit 0
        fi
    fi
    
    # Method 2: Try as postgres user (will prompt for password)
    echo ""
    echo "If the above failed, please run manually as postgres user:"
    echo "  psql -U postgres -d $DB_NAME -f backend/migrations/add_strategy_type.sql"
    echo ""
    echo "Or if you know the postgres password:"
    echo "  PGPASSWORD=your_password psql -U postgres -d $DB_NAME -f backend/migrations/add_strategy_type.sql"
else
    echo "psql not found. Please install PostgreSQL client tools."
    exit 1
fi

