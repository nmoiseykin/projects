# SQL Query Monitoring Scripts

## Available Scripts

### 1. `show-running-queries.sh`
Shows all currently running SQL queries with details.

**Usage:**
```bash
./show-running-queries.sh
```

**Shows:**
- All active queries with duration
- Query statistics by state
- Long running queries (> 5 seconds)
- Blocked queries
- Database locks

### 2. `watch-queries.sh`
Real-time monitoring of SQL queries (updates every 2 seconds by default).

**Usage:**
```bash
./watch-queries.sh          # Updates every 2 seconds
./watch-queries.sh 5        # Updates every 5 seconds
```

**Press Ctrl+C to stop**

### 3. `show-backtest-queries.sh`
Shows only queries related to backtest execution.

**Usage:**
```bash
./show-backtest-queries.sh
```

**Shows:**
- Active backtest queries
- Query performance statistics
- Long running backtest queries (> 10 seconds)

## Examples

### Check what's running right now
```bash
./show-running-queries.sh
```

### Watch queries in real-time
```bash
./watch-queries.sh
```

### Monitor backtest execution
```bash
./show-backtest-queries.sh
```

## Killing Queries

If you need to kill a stuck query:

```bash
# Get the PID from the script output
./show-running-queries.sh

# Then connect to database and kill it
PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db -c "SELECT pg_terminate_backend(<pid>);"
```

Or use the PID directly:
```bash
# Find the PID
./show-running-queries.sh | grep <query_pattern>

# Kill it (be careful!)
PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db -c "SELECT pg_terminate_backend(<pid>);"
```

## Understanding the Output

- **pid**: Process ID of the query
- **state**: Query state (active, idle, idle in transaction, etc.)
- **duration_sec**: How long the query has been running
- **query_preview**: First part of the SQL query
- **wait_event**: What the query is waiting for (if any)

## Common States

- **active**: Query is currently executing
- **idle**: Connection is open but no query running
- **idle in transaction**: Transaction is open but no query running
- **idle in transaction (aborted)**: Transaction failed and is waiting for rollback

## Tips

1. **Long running queries** during backtests are normal - they're processing large datasets
2. **Blocked queries** indicate locks - check the blocking query
3. **High duration** queries might need optimization or cancellation
4. Use `watch-queries.sh` to monitor backtest progress in real-time


