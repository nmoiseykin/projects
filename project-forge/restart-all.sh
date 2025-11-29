#!/bin/bash
# Restart all Project Forge services

set -e

cd ~/projects/project-forge

echo "🔄 Restarting Project Forge..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Stop everything
echo "1️⃣  Stopping all services..."
echo ""

# Stop Docker containers
if command -v docker &> /dev/null; then
    echo "   Stopping Docker containers..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.localdb.yml down 2>/dev/null || true
fi

# Stop API processes
echo "   Stopping API processes..."
API_PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}' || true)
if [ -n "$API_PIDS" ]; then
    for PID in $API_PIDS; do
        echo "   Killing API process $PID..."
        sudo kill $PID 2>/dev/null || kill $PID 2>/dev/null || sudo kill -9 $PID 2>/dev/null || true
    done
    sleep 2
fi

# Stop web processes (Next.js)
echo "   Stopping web processes..."
WEB_PIDS=$(ps aux | grep "next dev" | grep -v grep | awk '{print $2}' || true)
if [ -n "$WEB_PIDS" ]; then
    for PID in $WEB_PIDS; do
        echo "   Killing web process $PID..."
        kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
    done
    sleep 2
fi

echo "   ✅ All services stopped"
echo ""

# Step 2: Check database tables
echo "2️⃣  Checking database tables..."
TABLE_COUNT=$(PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'backtest_%';" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$TABLE_COUNT" != "3" ]; then
    echo "   ⚠️  Tables don't exist or incomplete (found $TABLE_COUNT, expected 3)"
    echo "   Creating tables..."
    
    if [ -f "create-tables.sql" ]; then
        if sudo -u postgres psql -d aurora_db -f create-tables.sql > /dev/null 2>&1; then
            echo "   ✅ Tables created"
        else
            echo -e "   ${YELLOW}⚠️  Could not create tables automatically${NC}"
            echo "   Please run manually: sudo -u postgres psql -d aurora_db -f create-tables.sql"
        fi
    else
        echo -e "   ${RED}❌ create-tables.sql not found!${NC}"
    fi
else
    echo "   ✅ Database tables exist"
fi
echo ""

# Step 3: Verify .env exists
echo "3️⃣  Checking configuration..."
if [ ! -f .env ]; then
    echo -e "   ${YELLOW}⚠️  .env file not found${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "   Created .env from template"
        echo -e "   ${YELLOW}⚠️  Please edit .env with your database credentials!${NC}"
    else
        echo -e "   ${RED}❌ .env.example not found!${NC}"
        exit 1
    fi
else
    echo "   ✅ .env file exists"
fi
echo ""

# Step 4: Start API
echo "4️⃣  Starting API service..."
if [ -f "start-api.sh" ]; then
    ./start-api.sh
else
    echo "   Starting API manually..."
    cd backend
    
    # Load .env
    if [ -f ../.env ]; then
        export $(grep -v '^#' ../.env | xargs)
    fi
    
    # Activate venv if exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start API
    cd ..
    nohup bash -c "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" > logs/api.log 2>&1 &
    API_PID=$!
    echo "   ✅ API started (PID: $API_PID)"
    echo "   📝 Logs: logs/api.log"
fi

sleep 3

# Step 5: Start Web (if needed)
echo ""
echo "5️⃣  Checking web service..."
if [ -d "frontend" ]; then
    # Check if web is already running
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "   ✅ Web is already running on port 3000"
    else
        echo "   Starting web service..."
        cd frontend
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            echo "   Installing dependencies..."
            npm install > /dev/null 2>&1 || echo "   ⚠️  npm install failed, continuing..."
        fi
        
        # Start Next.js
        nohup npm run dev > ../logs/web.log 2>&1 &
        WEB_PID=$!
        echo "   ✅ Web started (PID: $WEB_PID)"
        echo "   📝 Logs: logs/web.log"
        cd ..
    fi
else
    echo "   ⚠️  Frontend directory not found, skipping web service"
fi

sleep 3

# Step 6: Verify services
echo ""
echo "6️⃣  Verifying services..."
echo ""

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ API is healthy${NC} (http://localhost:8000)"
    
    # Check database connection in logs
    DB_CONN=$(tail -20 logs/api.log 2>/dev/null | grep -i "database" | tail -1 || echo "")
    if echo "$DB_CONN" | grep -q "localhost"; then
        echo -e "      ${GREEN}✅ Using localhost database${NC}"
    elif echo "$DB_CONN" | grep -q "host.docker.internal"; then
        echo -e "      ${YELLOW}⚠️  Still using host.docker.internal - may need manual restart${NC}"
    fi
else
    echo -e "   ${RED}❌ API is not responding${NC}"
    echo "      Check logs: tail -f logs/api.log"
fi

# Check Web
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Web is running${NC} (http://localhost:3000)"
else
    echo -e "   ${YELLOW}⚠️  Web may still be starting${NC}"
    echo "      Check logs: tail -f logs/web.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Restart complete!${NC}"
echo ""
echo "📍 Access your application:"
echo "   • Frontend: http://localhost:3000"
echo "   • API:      http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • API: tail -f ~/projects/project-forge/logs/api.log"
echo "   • Web: tail -f ~/projects/project-forge/logs/web.log"
echo ""
echo "🔄 To restart again, run:"
echo "   cd ~/projects/project-forge && ./restart-all.sh"
echo ""


