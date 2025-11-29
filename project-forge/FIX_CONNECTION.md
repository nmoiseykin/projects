# 🔧 Fix Database Connection Error

## The Problem
The API is trying to connect to `host.docker.internal` instead of `localhost`, which causes "Connection refused" errors.

## The Solution

### Step 1: Stop the Old API Process

The old API process is running as root. You need to stop it manually:

```bash
# Find the process
ps aux | grep "uvicorn app.main:app" | grep -v grep

# Stop it (you'll need sudo password)
sudo kill 29356

# Or if that doesn't work:
sudo kill -9 29356
```

### Step 2: Create Database Tables

```bash
cd ~/projects/project-forge
sudo -u postgres psql -d aurora_db -f create-tables.sql
```

### Step 3: Start API with Correct Configuration

```bash
cd ~/projects/project-forge
./start-api.sh
```

This script will:
- Load `.env` from the project root
- Set `DB_HOST=localhost` correctly
- Start the API with the right environment

### Step 4: Verify

```bash
# Check API is using localhost
tail -20 logs/api.log | grep -i "database"

# Should show: Database: localhost:5432/aurora_db

# Test connection
curl http://localhost:8000/health
```

## ✅ What Was Fixed

1. **Config file** - Now uses absolute path to `.env` file
2. **Start script** - `start-api.sh` loads environment variables correctly
3. **Database tables** - SQL script ready to create tables

## 🎯 After These Steps

1. Tables will exist
2. API will connect to `localhost` (not `host.docker.internal`)
3. Backtest execution should work!

---

**Quick Command Summary:**
```bash
# Stop old API
sudo kill $(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')

# Create tables
sudo -u postgres psql -d aurora_db -f create-tables.sql

# Start new API
./start-api.sh
```


