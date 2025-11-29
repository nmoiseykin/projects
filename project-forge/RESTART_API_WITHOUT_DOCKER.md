# Restart API Without Docker

Since Docker is having connection issues, here's how to restart the API service manually:

## 🔄 Restart API Service (Manual)

### Step 1: Find the Running Process

```bash
# Find uvicorn process
ps aux | grep uvicorn | grep -v grep
```

### Step 2: Restart It

**Option A: If running in Docker (but Docker has issues):**
```bash
# Try to restart (may fail if Docker not working)
docker-compose restart api

# If that fails, you need to fix Docker first (see below)
```

**Option B: If running manually (not in Docker):**
```bash
# Kill the process (replace PID with actual process ID)
kill <PID>

# Then restart
cd ~/projects/project-forge/backend
source venv/bin/activate  # if using venv
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Fix Docker First (Recommended)

### Quick Fix:

```bash
# 1. Start Docker service
sudo service docker start

# 2. Add user to docker group
sudo usermod -aG docker $USER

# 3. Apply changes
newgrp docker

# 4. Test
docker ps

# 5. Then restart API
cd ~/projects/project-forge
docker-compose restart api
```

### Or Use Docker Desktop:

1. **Open Docker Desktop in Windows**
2. **Settings → Resources → WSL Integration**
3. **Enable your WSL2 distro**
4. **Apply & Restart**
5. Then: `docker-compose restart api`

## ✅ Verify API is Running

After restarting, check:

```bash
# Test API
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

## 🎯 Current Status

Your API is currently running (we confirmed earlier), but you need to restart it to pick up the API key fix.

**The easiest way:**
1. Fix Docker connection (see above)
2. Run: `docker-compose restart api`
3. Try generating scenarios again


