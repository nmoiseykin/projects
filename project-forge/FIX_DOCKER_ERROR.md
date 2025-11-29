# Fix Docker Error: "Not supported URL scheme http+docker"

## 🔴 Error

```
docker.errors.DockerException: Error while fetching server API version: Not supported URL scheme http+docker
```

This means Docker can't connect to the Docker daemon.

## ✅ Solutions

### Solution 1: Start Docker Service (Most Common)

```bash
# Start Docker service
sudo service docker start

# Verify it's running
sudo service docker status

# Test Docker
docker ps
```

### Solution 2: Use Docker Desktop (Recommended for WSL2)

If you have Docker Desktop installed:

1. **Make sure Docker Desktop is running in Windows**
2. **Enable WSL2 integration:**
   - Open Docker Desktop
   - Go to Settings → Resources → WSL Integration
   - Enable integration with your WSL2 distro
   - Click "Apply & Restart"

3. **Then test:**
   ```bash
   docker ps
   ```

### Solution 3: Fix Docker Socket Permissions

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (choose one):
# Option A: Log out and back in to WSL2
# Option B: Run this command:
newgrp docker

# Test
docker ps
```

### Solution 4: Reset Docker Environment

```bash
# Unset any problematic environment variables
unset DOCKER_HOST
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH

# Test
docker ps
```

## 🔧 Step-by-Step Fix

### Quick Fix Script

Run these commands in order:

```bash
# 1. Start Docker service
sudo service docker start

# 2. Wait a moment
sleep 2

# 3. Add user to docker group (if needed)
sudo usermod -aG docker $USER
newgrp docker

# 4. Test Docker
docker ps

# 5. If that works, try your project
cd ~/projects/project-forge
docker-compose ps
```

## 🎯 Recommended: Use Docker Desktop

For WSL2, **Docker Desktop is the easiest solution:**

1. **Install Docker Desktop for Windows** (if not installed):
   - Download: https://www.docker.com/products/docker-desktop/

2. **Enable WSL2 Integration:**
   - Open Docker Desktop
   - Settings → Resources → WSL Integration
   - Enable your WSL2 distro
   - Apply & Restart

3. **Verify:**
   ```bash
   docker ps
   # Should work without sudo
   ```

## 🐛 Alternative: Manual Docker Service

If you prefer not to use Docker Desktop:

```bash
# Start Docker service
sudo service docker start

# Make it start automatically
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker ps
```

## ✅ Verify Fix

After applying a solution:

```bash
# Test Docker
docker ps

# Should return (empty list is OK):
# CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

# Test docker-compose
docker-compose --version
# Should show version number
```

## 📝 Quick Reference

| Issue | Solution |
|-------|----------|
| Docker daemon not running | `sudo service docker start` |
| Permission denied | `sudo usermod -aG docker $USER && newgrp docker` |
| WSL2 integration | Enable in Docker Desktop settings |
| Environment variables | `unset DOCKER_HOST` |

---

**TL;DR:** Start Docker service with `sudo service docker start` or use Docker Desktop with WSL2 integration enabled.


