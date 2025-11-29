# Fix Database Connection Error

## 🔴 Error: "[Errno 111] Connection refused"

This means the API cannot connect to your PostgreSQL database.

## ✅ Solutions

### Solution 1: Check PostgreSQL is Running

```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Or
systemctl status postgresql

# If not running, start it:
sudo service postgresql start
```

### Solution 2: Verify Database Connection Settings

Check your `.env` file:

```bash
cd ~/projects/project-forge
cat .env | grep "^DB_"
```

Should show:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aurora_db
DB_USER=aurora_user
DB_PASSWORD=aurora_pass123
```

### Solution 3: Test Database Connection

```bash
# Test connection
psql -h localhost -U aurora_user -d aurora_db -c "SELECT 1;"

# If this fails, check:
# 1. PostgreSQL is running
# 2. User/password are correct
# 3. Database exists
```

### Solution 4: If Using Docker for API

If your API is running in Docker, it needs special configuration to access host PostgreSQL:

**Check docker-compose.localdb.yml:**
- Should use `host.docker.internal` or `172.17.0.1` for DB_HOST
- Or use your WSL2 IP address

**Get WSL2 IP:**
```bash
ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1
```

Then update `.env`:
```bash
DB_HOST=<WSL2_IP>
```

### Solution 5: Create Database if Missing

```bash
# Connect as postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE aurora_db;
CREATE USER aurora_user WITH PASSWORD 'aurora_pass123';
GRANT ALL PRIVILEGES ON DATABASE aurora_db TO aurora_user;
\q
```

## 🔧 Quick Diagnostic

Run this to check everything:

```bash
cd ~/projects/project-forge

echo "=== Database Configuration ==="
cat .env | grep "^DB_"

echo ""
echo "=== PostgreSQL Status ==="
sudo service postgresql status 2>/dev/null || systemctl status postgresql 2>/dev/null || echo "Cannot check (need sudo)"

echo ""
echo "=== Test Connection ==="
psql -h localhost -U aurora_user -d aurora_db -c "SELECT 1;" 2>&1 | head -3
```

## 🎯 Most Likely Fix

**If API is in Docker and DB is on host:**

Update `.env` or `docker-compose.localdb.yml`:

```bash
# Get WSL2 IP
WSL_IP=$(ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1)

# Update .env
DB_HOST=$WSL_IP
```

Or use `host.docker.internal` (already in docker-compose.localdb.yml).

## ✅ After Fixing

1. Restart API service
2. Test connection: `curl http://localhost:8000/health`
3. Try executing backtest again

---

**TL;DR:** PostgreSQL isn't accessible. Check it's running and connection settings are correct.


