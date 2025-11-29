# 🔧 Quick Fix: Database Connection Error

## The Problem
Error: `[Errno 111] Connection refused` when executing backtest.

## The Solution

### Step 1: Create Database Tables

Run this command (you'll need to enter your sudo password):

```bash
cd ~/projects/project-forge
sudo -u postgres psql -d aurora_db -f create-tables.sql
```

**OR** run the setup script:

```bash
./setup-database.sh
```

### Step 2: Verify Tables Were Created

```bash
PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db -c "\dt backtest_*"
```

You should see:
- `backtest_runs`
- `backtest_scenarios`  
- `backtest_results`

### Step 3: Restart API (if needed)

```bash
./restart-api.sh
```

### Step 4: Try Again

Go back to your browser and try executing the backtest again.

---

## ✅ What I Fixed

1. **Config file** - Now reads `.env` from the correct location (project root)
2. **Database tables** - Created SQL script to set up tables with proper permissions
3. **API restart** - Script to restart the API service

## 🎯 Next Steps

After tables are created, the backtest execution should work! The API is already running and healthy at `http://localhost:8000`.


