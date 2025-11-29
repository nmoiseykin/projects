# Docker Compose Error Fix

## 🔴 Error You're Seeing

```
Traceback (most recent call last):
  File "/usr/bin/docker-compose", line 33, in <module>
    ...
  File "/usr/lib/python3/dist-packages/compose/cli/docker_client.py", line 41, in get_client
    client = docker_client(
```

This error means:
1. **Docker daemon is not running**, OR
2. You're using old `docker-compose` (Python package) instead of new `docker compose` (plugin)

## ✅ Solutions

### Solution 1: Start Docker Service

```bash
# Start Docker service
sudo service docker start

# Verify it's running
sudo service docker status

# Test Docker
docker ps
```

### Solution 2: Use New Docker Compose Command

The old `docker-compose` (with hyphen) is deprecated. Use `docker compose` (without hyphen):

```bash
# Instead of:
docker-compose up

# Use:
docker compose up
```

### Solution 3: Install Docker Compose Plugin

If you don't have `docker compose` plugin:

```bash
# Install Docker Compose plugin
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Verify
docker compose version
```

### Solution 4: Use Docker Desktop (Easiest)

If you have Docker Desktop installed in Windows:
1. Make sure Docker Desktop is running
2. Enable WSL2 integration in Docker Desktop settings
3. Then use `docker compose` command

## 🔧 Step-by-Step Fix

### Step 1: Check Docker Status

```bash
# Check if Docker is running
sudo service docker status

# If not running, start it
sudo service docker start
```

### Step 2: Test Docker Connection

```bash
# Test Docker
docker ps

# If you get "Cannot connect to Docker daemon", continue to Step 3
```

### Step 3: Fix Docker Permissions (if needed)

```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, OR
newgrp docker

# Test again
docker ps
```

### Step 4: Use Correct Command

```bash
cd ~/projects/project-forge

# Try new command (recommended)
docker compose up

# OR if you must use old command
docker-compose up
```

## 🎯 Quick Fix Commands

Run these in order:

```bash
# 1. Start Docker
sudo service docker start

# 2. Add user to docker group (if needed)
sudo usermod -aG docker $USER
newgrp docker

# 3. Test Docker
docker ps

# 4. Use new compose command
cd ~/projects/project-forge
docker compose up
```

## 📝 Update docker-compose.yml Usage

If you want to use the new `docker compose` command everywhere, you can create an alias:

```bash
# Add to ~/.bashrc
echo 'alias docker-compose="docker compose"' >> ~/.bashrc
source ~/.bashrc

# Now both commands work
docker-compose up  # Uses docker compose under the hood
docker compose up  # Direct command
```

## 🐛 Common Issues

### Issue: "Cannot connect to Docker daemon"

**Fix:**
```bash
sudo service docker start
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: "Permission denied"

**Fix:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Old docker-compose version

**Fix:**
```bash
# Use new command
docker compose up

# Or install plugin
sudo apt-get install docker-compose-plugin
```

## ✅ Verify Everything Works

```bash
# 1. Docker running
docker ps

# 2. Compose available
docker compose version

# 3. Start services
cd ~/projects/project-forge
docker compose up -d

# 4. Check services
docker compose ps
```

---

**TL;DR:** Start Docker service (`sudo service docker start`) and use `docker compose` instead of `docker-compose`.


