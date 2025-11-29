#!/bin/bash
# Complete fix for database connection issues

set -e

cd ~/projects/project-forge

echo "🔧 Fixing Database Connection Issues..."
echo ""

# Step 1: Stop old API processes
echo "1️⃣  Stopping old API processes..."
OLD_PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}' || true)
if [ -n "$OLD_PIDS" ]; then
    echo "   Found processes: $OLD_PIDS"
    echo "   ⚠️  You'll need to stop these manually with sudo:"
    for PID in $OLD_PIDS; do
        echo "      sudo kill $PID"
    done
    echo ""
    read -p "   Press Enter after stopping the processes, or Ctrl+C to cancel..."
else
    echo "   ✅ No old processes found"
fi

# Step 2: Create database tables
echo ""
echo "2️⃣  Creating database tables..."
if [ -f "create-tables.sql" ]; then
    echo "   Running: sudo -u postgres psql -d aurora_db -f create-tables.sql"
    if sudo -u postgres psql -d aurora_db -f create-tables.sql; then
        echo "   ✅ Tables created"
    else
        echo "   ❌ Failed to create tables"
        echo "   Please run manually: sudo -u postgres psql -d aurora_db -f create-tables.sql"
        exit 1
    fi
else
    echo "   ❌ create-tables.sql not found!"
    exit 1
fi

# Step 3: Verify tables
echo ""
echo "3️⃣  Verifying tables..."
TABLE_COUNT=$(PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'backtest_%';" 2>/dev/null | tr -d ' ')
if [ "$TABLE_COUNT" = "3" ]; then
    echo "   ✅ All tables exist ($TABLE_COUNT found)"
else
    echo "   ⚠️  Expected 3 tables, found $TABLE_COUNT"
fi

# Step 4: Start API
echo ""
echo "4️⃣  Starting API with correct configuration..."
if [ -f "start-api.sh" ]; then
    ./start-api.sh
else
    echo "   ❌ start-api.sh not found!"
    exit 1
fi

echo ""
echo "✅ Fix complete!"
echo ""
echo "🧪 Testing..."
sleep 2
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is healthy!"
    echo ""
    echo "📊 Check database connection in logs:"
    tail -5 logs/api.log | grep -i "database" || echo "   (No database log found yet)"
else
    echo "⚠️  API may still be starting. Check logs: tail -f logs/api.log"
fi


