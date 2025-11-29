# Virtual Environment (venv) Usage Guide

## Do I Need to Use venv?

### ✅ **When Using Docker (Recommended)**
**NO, you don't need venv!**

When you run `./start.sh` or use `docker-compose`, everything runs inside Docker containers:
- Backend Python code runs in the `api` container
- Frontend Node.js runs in the `web` container
- All dependencies are installed inside the containers

**You can ignore venv completely when using Docker.**

---

### ⚠️ **When Running Backend Manually (Without Docker)**
**YES, you need venv!**

If you want to run the backend API directly on your machine (not in Docker):

```bash
cd ~/projects/project-forge/backend

# Create venv (first time only)
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Why?** The venv isolates your project's Python packages from system packages, preventing conflicts.

---

## Quick Reference

### Using Docker (No venv needed)
```bash
# Start everything
./start.sh

# Or manually
docker-compose up -d
```

### Running Backend Manually (venv required)
```bash
cd backend
source venv/bin/activate  # Activate venv
uvicorn app.main:app --reload
```

### Running Database Setup Scripts (venv required if not using Docker)
```bash
cd backend
source venv/bin/activate  # Activate venv
python init_db.py
python create_tables.py
```

---

## Summary

| Scenario | Need venv? | Why |
|----------|-----------|-----|
| Using `./start.sh` or `docker-compose` | ❌ No | Everything runs in containers |
| Running backend manually | ✅ Yes | Isolates dependencies |
| Running database scripts manually | ✅ Yes | Scripts need Python packages |
| Running frontend manually | ❌ No | Frontend uses npm, not Python |

**Recommendation:** Use Docker (`./start.sh`) - it's simpler and you don't need to worry about venv!

