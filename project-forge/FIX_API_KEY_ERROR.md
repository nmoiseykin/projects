# Fix "Invalid API key" Error

## ✅ What I Fixed

The backend wasn't properly extracting the `X-API-KEY` header from requests. I've updated the code to use FastAPI's `Header` function.

## 🔄 Restart Required

**You need to restart the API service for the fix to take effect:**

### If using Docker:
```bash
cd ~/projects/project-forge
docker-compose restart api
```

### If running manually:
```bash
# Stop the uvicorn process (Ctrl+C)
# Then restart:
cd ~/projects/project-forge/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## ✅ Verify It Works

After restarting, test the API:

```bash
# Test with curl
curl -X POST http://localhost:8000/api/ai/suggest \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: dev-key-change-in-production" \
  -d '{"context": "test"}'
```

## 🔍 Current Configuration

- **Backend API_KEY:** `dev-key-change-in-production` (from .env)
- **Frontend sends:** `dev-key-change-in-production` (default or from NEXT_PUBLIC_API_KEY)

They should match! ✅

## 📝 What Changed

**Before:**
```python
def verify_api_key(x_api_key: str = None):
    # Header wasn't being extracted properly
```

**After:**
```python
def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")):
    # Now properly extracts X-API-KEY header
```

## 🎯 Next Steps

1. **Restart API service** (see commands above)
2. **Try generating scenarios again** in the browser
3. **Should work now!** ✅

---

**The fix is applied. Just restart the API service and try again!**


