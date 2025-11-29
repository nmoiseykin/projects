# Database Safety - Your Existing Tables Are Safe! ✅

## 🛡️ Your Existing PostgreSQL Database is Protected

**Short answer: YES, your existing tables are completely safe. The project will NOT drop or modify them.**

## 📊 What This Project Does

### 1. **Reads from Your Existing Table**
- The project **ONLY READS** from `market.ohlcv_data`
- It **NEVER modifies, drops, or deletes** this table
- All queries are SELECT statements (read-only for your data)

### 2. **Creates Its Own Tables**
- The project creates **NEW tables** for its own use:
  - `backtest_runs`
  - `backtest_scenarios`
  - `backtest_results`
- These are **separate** from your existing tables
- They won't interfere with your data

### 3. **No Automatic Migrations**
- No Alembic migrations run automatically
- No DROP TABLE statements in the code
- No schema modifications to existing tables

## 🔧 Two Ways to Use the Project

### Option 1: Use Docker Database (Recommended - Safest)

If you use `docker-compose up` with the `db` service:

```yaml
# docker-compose.yml creates a SEPARATE database container
db:
  image: postgres:14
  # This is a completely isolated database
```

**Result:**
- ✅ Creates a **separate PostgreSQL container**
- ✅ Your existing local PostgreSQL is **untouched**
- ✅ 100% safe - completely isolated

**To use this:**
```bash
# Just run docker-compose
docker-compose up
# Your local PostgreSQL is never touched
```

### Option 2: Use Your Existing Local PostgreSQL

If you want to use your existing database:

**In `.env` file:**
```bash
DB_HOST=localhost          # Your existing PostgreSQL
DB_PORT=5432               # Your existing port
DB_NAME=your_existing_db   # Your existing database name
DB_USER=your_user          # Your existing user
DB_PASSWORD=your_pass      # Your existing password
```

**What happens:**
1. ✅ Connects to your existing database
2. ✅ **ONLY READS** from `market.ohlcv_data` (read-only)
3. ✅ Creates new tables: `backtest_runs`, `backtest_scenarios`, `backtest_results`
4. ✅ **NEVER drops or modifies** your existing tables

## 📋 Tables Created by This Project

If you use your existing database, these tables will be created:

```sql
-- These are NEW tables, separate from your existing ones
backtest_runs          -- Stores backtest run metadata
backtest_scenarios     -- Stores scenario parameters
backtest_results       -- Stores backtest results
```

**Your existing tables remain untouched!**

## 🔍 Code Analysis

### What the Code Does:

1. **SQL Templates** (`backend/app/sql/base_templates/`):
   - Only SELECT queries
   - Read from `market.ohlcv_data`
   - No INSERT, UPDATE, DELETE, or DROP

2. **ORM Models** (`backend/app/models/orm.py`):
   - Define table structures
   - Used by SQLAlchemy to create tables
   - **No DROP statements**

3. **No Auto-Migrations**:
   - Alembic is installed but **not configured**
   - No migration files exist
   - No automatic schema changes

## ✅ Safety Checklist

- ✅ No DROP TABLE statements
- ✅ No TRUNCATE statements
- ✅ No DELETE from your tables
- ✅ No UPDATE to your tables
- ✅ Only SELECT from `market.ohlcv_data`
- ✅ Creates only new tables (backtest_*)
- ✅ No automatic migrations

## 🎯 Recommended Setup

### For Maximum Safety:

**Use Docker database (Option 1):**

1. **Don't start the `db` service:**
   ```bash
   # Start only API and Web
   docker-compose up api web
   ```

2. **Or modify docker-compose.yml:**
   ```yaml
   # Comment out the db service
   # db:
   #   image: postgres:14
   #   ...
   ```

3. **Connect to your existing PostgreSQL:**
   ```bash
   # In .env
   DB_HOST=localhost
   DB_NAME=your_existing_database
   ```

### Or Use Separate Database:

Create a **new database** for this project:

```sql
-- In your existing PostgreSQL
CREATE DATABASE project_forge;

-- Then in .env
DB_NAME=project_forge
```

This way:
- ✅ Your existing database is completely separate
- ✅ Project uses its own database
- ✅ Zero risk to your data

## 🔒 Final Assurance

**The project:**
- ✅ **Reads** from `market.ohlcv_data` (read-only)
- ✅ **Creates** new tables for its own use
- ✅ **Never drops** any tables
- ✅ **Never modifies** your existing tables
- ✅ **Never runs** automatic migrations

**Your existing tables are 100% safe!**

---

## 📝 Summary

| Action | Your Tables | Project Tables |
|--------|-------------|----------------|
| Read | ✅ Reads from `market.ohlcv_data` | N/A |
| Create | ❌ Never creates | ✅ Creates `backtest_*` tables |
| Drop | ❌ Never drops | ❌ Never drops |
| Modify | ❌ Never modifies | ✅ Only inserts/updates its own data |

**Bottom line: Your existing PostgreSQL database and tables are completely safe!**


