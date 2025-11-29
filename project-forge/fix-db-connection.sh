#!/bin/bash
# Fix database connection issues

echo "🔧 Fixing Database Connection..."
echo ""

cd ~/projects/project-forge

# 1. Check PostgreSQL is running
echo "1️⃣  Checking PostgreSQL..."
if netstat -tuln 2>/dev/null | grep -q ":5432" || ss -tuln 2>/dev/null | grep -q ":5432"; then
    echo "   ✅ PostgreSQL is running"
else
    echo "   ❌ PostgreSQL is NOT running"
    echo "   Start it: sudo service postgresql start"
    exit 1
fi

# 2. Test connection
echo ""
echo "2️⃣  Testing database connection..."
source .env 2>/dev/null || true
if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &>/dev/null; then
    echo "   ✅ Connection works!"
else
    echo "   ❌ Connection failed"
    echo "   Check .env file and PostgreSQL credentials"
    exit 1
fi

# 3. Create tables if they don't exist
echo ""
echo "3️⃣  Checking database tables..."
TABLE_COUNT=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'backtest_%';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" = "0" ] || [ -z "$TABLE_COUNT" ]; then
    echo "   ⚠️  Tables don't exist. Creating them..."
    
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python3 init_db.py
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Tables created!"
    else
        echo "   ❌ Failed to create tables"
        echo "   Try manual SQL (see INIT_DATABASE.md)"
    fi
else
    echo "   ✅ Tables exist ($TABLE_COUNT found)"
fi

echo ""
echo "✅ Database setup complete!"
echo ""
echo "🔄 Now restart the API service:"
echo "   ./restart-api.sh"
echo "   Or if using Docker: docker-compose restart api"


