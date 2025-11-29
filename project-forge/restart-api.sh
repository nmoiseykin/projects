#!/bin/bash
# Restart API service manually

echo "🔄 Restarting API Service..."
echo ""

# Find uvicorn process
PID=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$PID" ]; then
    echo "❌ API process not found"
    echo "   Starting API manually..."
    cd ~/projects/project-forge/backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    echo "✅ API started"
else
    echo "📋 Found API process: PID $PID"
    echo "🔄 Restarting..."
    
    # Kill the process
    kill $PID
    sleep 2
    
    # Start it again
    cd ~/projects/project-forge/backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
    
    echo "✅ API restarted"
    echo "📝 Logs: /tmp/api.log"
fi

sleep 3

# Test
echo ""
echo "🧪 Testing API..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is responding!"
else
    echo "❌ API not responding yet. Check logs: /tmp/api.log"
fi


