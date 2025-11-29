# WSL2 + Docker Setup Guide

## 🌐 Accessing from Windows Browser

Since you're using **WSL2** with Docker running inside it, here's how to access the application from your Windows browser.

## Network Configuration

### How WSL2 Networking Works

1. **WSL2 has its own virtual network**
   - WSL2 IP is different from Windows localhost
   - Docker containers run inside WSL2
   - Ports are automatically forwarded to Windows

2. **Port Forwarding**
   - Docker Compose exposes ports to WSL2
   - WSL2 automatically forwards to Windows
   - You can access via `localhost` from Windows

## ✅ Current Configuration

The `docker-compose.yml` is already configured correctly:

```yaml
services:
  db:
    ports:
      - "5432:5432"  # ✅ Exposed to WSL2, forwarded to Windows
  
  api:
    ports:
      - "8000:8000"  # ✅ Exposed to WSL2, forwarded to Windows
  
  web:
    ports:
      - "3000:3000"  # ✅ Exposed to WSL2, forwarded to Windows
```

## 🚀 Accessing from Windows Browser

### Option 1: Use localhost (Recommended)

From your **Windows browser**, access:

- **Frontend**: http://localhost:3000
- **API**: http://localhost:3000/api
- **API Docs**: http://localhost:8000/docs

WSL2 automatically forwards these ports to Windows.

### Option 2: Use WSL2 IP Address

If `localhost` doesn't work, find your WSL2 IP:

```bash
# In WSL2 terminal
ip addr show eth0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1
```

Then access:
- **Frontend**: http://<WSL2_IP>:3000
- **API**: http://<WSL2_IP>:8000

## 🔧 Troubleshooting

### Port Not Accessible from Windows

1. **Check if ports are listening in WSL2:**
   ```bash
   # In WSL2
   netstat -tuln | grep -E "3000|8000|5432"
   ```

2. **Check Windows firewall:**
   - Windows Firewall might block ports
   - Add exception for ports 3000, 8000, 5432

3. **Verify Docker is running:**
   ```bash
   # In WSL2
   docker ps
   ```

4. **Check WSL2 port forwarding:**
   ```powershell
   # In Windows PowerShell (as Admin)
   netsh interface portproxy show all
   ```

### Frontend Can't Connect to API

If the frontend can't reach the API from Windows browser:

1. **Update frontend API URL** (if needed):
   ```typescript
   // frontend/lib/api.ts
   const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
   ```

2. **Or use WSL2 hostname:**
   ```bash
   # Get WSL2 hostname
   hostname
   # Then use: http://<hostname>:8000/api
   ```

## 📝 Step-by-Step Setup

### 1. Start Docker in WSL2

```bash
# In WSL2 terminal
cd ~/projects/project-forge

# Make sure Docker is running
sudo service docker start

# Or if using Docker Desktop
# Docker Desktop should be running in Windows
```

### 2. Start Services

```bash
# In WSL2 terminal
docker-compose up -d
```

### 3. Access from Windows

Open **Windows browser** and go to:
- http://localhost:3000 (Frontend)
- http://localhost:8000/docs (API Documentation)

## 🔍 Verify Everything Works

### Check Services in WSL2

```bash
# In WSL2
docker-compose ps
# Should show all 3 services running
```

### Test API from WSL2

```bash
# In WSL2
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Test from Windows PowerShell

```powershell
# In Windows PowerShell
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

## 🐛 Common Issues

### Issue: "Connection Refused" from Windows

**Solution:**
1. Make sure Docker is running in WSL2
2. Check if services are actually running: `docker-compose ps`
3. Verify ports are exposed: `docker-compose port api 8000`

### Issue: Frontend loads but API calls fail

**Solution:**
1. Check `NEXT_PUBLIC_API_URL` in frontend
2. Make sure it's `http://localhost:8000/api` (not `http://127.0.0.1`)
3. Check browser console for CORS errors

### Issue: Database connection fails

**Solution:**
1. Database is only accessible from WSL2/containers
2. If you need to connect from Windows, use WSL2 IP:
   ```
   Host: <WSL2_IP>
   Port: 5432
   ```

## 🎯 Quick Reference

| Service | WSL2 Access | Windows Access |
|---------|-------------|----------------|
| Frontend | http://localhost:3000 | http://localhost:3000 ✅ |
| API | http://localhost:8000 | http://localhost:8000 ✅ |
| API Docs | http://localhost:8000/docs | http://localhost:8000/docs ✅ |
| Database | localhost:5432 | WSL2_IP:5432 (if needed) |

## 💡 Pro Tips

1. **Use Docker Desktop for Windows** (if available)
   - Better integration with Windows
   - Easier port management
   - GUI for monitoring

2. **Keep WSL2 terminal open**
   - View logs: `docker-compose logs -f`
   - Monitor services: `docker-compose ps`

3. **Windows Firewall**
   - May need to allow ports 3000, 8000
   - Usually auto-allows, but check if issues

4. **Hot Reload Works**
   - Code changes in WSL2 filesystem
   - Automatically reflected in Windows browser
   - No need to rebuild containers

---

## ✅ Summary

- **Docker runs in WSL2** ✅
- **Access from Windows browser via `localhost`** ✅
- **Ports automatically forwarded** ✅
- **No special configuration needed** ✅

Just run `docker-compose up` in WSL2 and access from Windows browser!


