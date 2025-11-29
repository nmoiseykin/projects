# Initialize Database Tables

## 🔴 Error: "Error executing backtest"

This error usually means the database tables don't exist yet. You need to create them first.

## ✅ Quick Fix

### Step 1: Create Database Tables

Run this script to create the required tables:

```bash
cd ~/projects/project-forge/backend

# If using virtual environment
source venv/bin/activate

# Run initialization script
python3 init_db.py
```

### Step 2: Verify Tables Created

```bash
# Connect to your database
psql -h localhost -U aurora_user -d aurora_db

# Check tables exist
\dt backtest_*

# Should show:
# - backtest_runs
# - backtest_scenarios  
# - backtest_results
```

### Step 3: Try Again

After creating tables, try executing the backtest again in the browser.

## 📋 Manual SQL (Alternative)

If the script doesn't work, create tables manually:

```sql
-- Connect to your database
psql -h localhost -U aurora_user -d aurora_db

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
```

## 🔍 Verify Database Connection

```bash
# Test connection
psql -h localhost -U aurora_user -d aurora_db -c "SELECT 1;"

# Should return: 1
```

## ✅ After Initialization

Once tables are created:
1. Restart API service (if needed)
2. Try executing backtest again
3. Should work now!

---

**TL;DR:** Run `python3 backend/init_db.py` to create the database tables.


