# Fix AI Scenario Generation Error

## 🔴 Error: "Error generating scenarios. Please try again."

I've improved error handling. Here's how to fix it:

## ✅ Quick Fix Steps

### Step 1: Restart API Service

The API service needs to be restarted to pick up the `.env` file changes:

```bash
cd ~/projects/project-forge

# Restart API service
docker-compose restart api

# Or restart all services
docker-compose restart
```

### Step 2: Check API Logs

```bash
# View API logs
docker-compose logs api | tail -50

# Watch logs in real-time
docker-compose logs -f api
```

### Step 3: Test API Directly

```bash
# Test the AI endpoint
curl -X POST http://localhost:8000/api/ai/suggest \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: dev-key-change-in-production" \
  -d '{"context": "test scenario generation"}'
```

## 🔍 What I Fixed

1. **Better Error Messages** - Now shows actual error details
2. **Improved Logging** - Backend logs show exact errors
3. **Frontend Error Display** - Shows specific error messages

## 🎯 Common Issues

### Issue 1: API Service Not Restarted

**Symptom:** API key is set but still getting errors

**Fix:**
```bash
docker-compose restart api
```

### Issue 2: Invalid API Key Format

**Check:**
```bash
cat .env | grep OPENAI_API_KEY
```

Should be:
```
OPENAI_API_KEY=sk-proj-...
```

**Fix:** Make sure key starts with `sk-` and is complete

### Issue 3: OpenAI API Error

**Check logs:**
```bash
docker-compose logs api | grep -i "openai\|error"
```

**Common errors:**
- "Invalid API key" → Get new key from OpenAI
- "Rate limit" → Wait a few minutes
- "Insufficient quota" → Check OpenAI billing

## 📝 Next Steps

1. **Restart API:**
   ```bash
   docker-compose restart api
   ```

2. **Try again in browser:**
   - Go to http://localhost:3000/chat
   - Enter your strategy description
   - Click "Generate Scenarios"

3. **Check browser console:**
   - Press F12
   - Go to Console tab
   - Look for detailed error messages

4. **Check API logs:**
   ```bash
   docker-compose logs -f api
   ```

## 🆘 Still Not Working?

Run this diagnostic:

```bash
cd ~/projects/project-forge

# 1. Check .env
echo "=== .env check ==="
cat .env | grep OPENAI_API_KEY

# 2. Check API health
echo "=== API health ==="
curl http://localhost:8000/health

# 3. Check API logs
echo "=== API logs ==="
docker-compose logs api | tail -20

# 4. Test AI endpoint
echo "=== Testing AI endpoint ==="
curl -X POST http://localhost:8000/api/ai/suggest \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: dev-key-change-in-production" \
  -d '{"context": "test"}' \
  -v
```

Send the output if you need more help!


