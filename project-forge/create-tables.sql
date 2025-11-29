-- Create database tables for Project Forge
-- Run this as postgres user: sudo -u postgres psql -d aurora_db -f create-tables.sql

-- Grant permissions first
GRANT ALL ON SCHEMA public TO aurora_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aurora_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aurora_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aurora_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aurora_user;

-- Create tables
CREATE TABLE IF NOT EXISTS backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'pending',
    total_scenarios INTEGER DEFAULT 0,
    completed_scenarios INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS backtest_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES backtest_runs(id) ON DELETE CASCADE,
    params JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES backtest_scenarios(id) ON DELETE CASCADE,
    grouping JSONB,
    totals JSONB,
    kpis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_scenarios_run_id ON backtest_scenarios(run_id);
CREATE INDEX IF NOT EXISTS idx_results_scenario_id ON backtest_results(scenario_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON backtest_runs(status);

-- Verify
SELECT 'Tables created successfully!' AS result;
\dt backtest_*


