# Troubleshooting AI Scenario Generation

## 🔴 Error: "Error generating scenarios. Please try again."

This error usually means one of these issues:

### 1. OpenAI API Key Not Set

**Check:**
```bash
cd ~/projects/project-forge
cat .env | grep OPENAI_API_KEY
```

**Fix:**
```bash
# Edit .env file
nano .env

# Add your OpenAI API key:
OPENAI_API_KEY=sk-your-actual-key-here
```

**Restart services:**
```bash
docker-compose restart api
```

### 2. Invalid OpenAI API Key

**Symptoms:**
- API key is set but still getting errors
- Check backend logs for authentication errors

**Fix:**
1. Get a valid API key from: https://platform.openai.com/api-keys
2. Update `.env` file
3. Restart API service

### 3. API Service Not Running

**Check:**
```bash
docker-compose ps
# Should show 'api' service as 'Up'
```

**Fix:**
```bash
# Restart API
docker-compose restart api

# Or restart all services
docker-compose restart
```

### 4. Network/Connection Issues

**Check backend logs:**
```bash
docker-compose logs api | tail -50
```

Look for:
- Connection errors
- Timeout errors
- API key errors

### 5. Check Browser Console

1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Try generating scenarios again
4. Check for error messages

## 🔍 Debugging Steps

### Step 1: Check .env File

```bash
cd ~/projects/project-forge
cat .env | grep -E "OPENAI|API_KEY"
```

Should show:
```
OPENAI_API_KEY=sk-...
API_KEY=dev-key-change-in-production
```

### Step 2: Check API is Running

```bash
# Test API health
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### Step 3: Check API Logs

```bash
# View recent logs
docker-compose logs api | tail -30

# Watch logs in real-time
docker-compose logs -f api
```

### Step 4: Test API Directly

```bash
# Test AI endpoint directly
curl -X POST http://localhost:8000/api/ai/suggest \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: dev-key-change-in-production" \
  -d '{"context": "test scenario"}'
```

### Step 5: Check Frontend Console

1. Open http://localhost:3000/chat
2. Open Browser DevTools (F12)
3. Go to Console tab
4. Try generating scenarios
5. Check for error messages

## ✅ Quick Fixes

### Fix 1: Add OpenAI API Key

```bash
cd ~/projects/project-forge

# Edit .env
nano .env

# Add this line (replace with your actual key):
OPENAI_API_KEY=sk-your-key-here

# Save and restart
docker-compose restart api
```

### Fix 2: Restart All Services

```bash
cd ~/projects/project-forge
docker-compose down
docker-compose up -d
```

### Fix 3: Check API Logs

```bash
docker-compose logs api | grep -i "error\|openai\|api"
```

## 🎯 Common Error Messages

### "AI service not configured"
- **Cause:** OPENAI_API_KEY not set in .env
- **Fix:** Add OPENAI_API_KEY to .env file

### "Invalid API key"
- **Cause:** OpenAI API key is invalid or expired
- **Fix:** Get new key from OpenAI dashboard

### "Connection timeout"
- **Cause:** Network issue or OpenAI API down
- **Fix:** Check internet connection, try again later

### "Rate limit exceeded"
- **Cause:** Too many API requests
- **Fix:** Wait a few minutes, check OpenAI usage limits

## 📝 Verification Checklist

- [ ] `.env` file exists in project root
- [ ] `OPENAI_API_KEY` is set in `.env`
- [ ] API key starts with `sk-`
- [ ] API service is running (`docker-compose ps`)
- [ ] Can access http://localhost:8000/health
- [ ] No errors in backend logs
- [ ] Browser console shows no errors

## 🆘 Still Not Working?

1. **Check all logs:**
   ```bash
   docker-compose logs
   ```

2. **Restart everything:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **Test API directly:**
   ```bash
   curl http://localhost:8000/api/ai/suggest \
     -X POST \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: dev-key-change-in-production" \
     -d '{"context": "test"}'
   ```

4. **Check OpenAI account:**
   - Verify API key is active
   - Check usage/billing limits
   - Ensure account has credits


