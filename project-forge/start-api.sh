#!/bin/bash
# Start API service with correct environment

cd ~/projects/project-forge/backend

# Load .env from project root
if [ -f ../.env ]; then
    # Clear any existing DB_* environment variables first
    unset DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
    
    # Load from .env file
    set -a
    source ../.env
    set +a
    
    echo "✅ Loaded .env from project root"
    echo "   DB_HOST: ${DB_HOST}"
    echo "   DB_NAME: ${DB_NAME}"
else
    echo "⚠️  .env file not found!"
    exit 1
fi

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start API
echo ""
echo "🚀 Starting API..."
echo "   Working directory: $(pwd)"
echo "   Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo ""

# Export environment variables explicitly for the uvicorn process
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD OPENAI_API_KEY APP_ENV API_KEY

# Start uvicorn with environment variables
nohup env DB_HOST="${DB_HOST}" DB_PORT="${DB_PORT}" DB_NAME="${DB_NAME}" DB_USER="${DB_USER}" DB_PASSWORD="${DB_PASSWORD}" OPENAI_API_KEY="${OPENAI_API_KEY}" APP_ENV="${APP_ENV:-dev}" API_KEY="${API_KEY}" uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &
API_PID=$!

echo "✅ API started with PID: $API_PID"
echo "📝 Logs: ~/projects/project-forge/logs/api.log"
echo ""
echo "Waiting for API to be ready..."
sleep 3

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is responding!"
else
    echo "⚠️  API may still be starting. Check logs: tail -f logs/api.log"
fi

