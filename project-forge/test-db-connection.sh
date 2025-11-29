#!/bin/bash
# Test database connection

echo "🔍 Testing Database Connection..."
echo ""

cd ~/projects/project-forge

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Configuration:"
echo "  DB_HOST: ${DB_HOST:-not set}"
echo "  DB_PORT: ${DB_PORT:-not set}"
echo "  DB_NAME: ${DB_NAME:-not set}"
echo "  DB_USER: ${DB_USER:-not set}"
echo ""

# Check PostgreSQL is running
echo "1️⃣  Checking PostgreSQL..."
if netstat -tuln 2>/dev/null | grep -q ":5432" || ss -tuln 2>/dev/null | grep -q ":5432"; then
    echo "   ✅ PostgreSQL is listening on port 5432"
else
    echo "   ❌ PostgreSQL is NOT listening on port 5432"
    echo "   Start PostgreSQL: sudo service postgresql start"
    exit 1
fi

# Test connection
echo ""
echo "2️⃣  Testing connection..."
if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" &>/dev/null; then
    echo "   ✅ Database connection successful!"
    
    # Check if tables exist
    echo ""
    echo "3️⃣  Checking tables..."
    TABLES=$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'backtest_%';" 2>/dev/null | tr -d ' ')
    
    if [ "$TABLES" = "3" ] || [ "$TABLES" = "0" ]; then
        echo "   Found $TABLES backtest tables"
        if [ "$TABLES" = "0" ]; then
            echo "   ⚠️  Tables don't exist. Run: python3 backend/init_db.py"
        else
            echo "   ✅ Tables exist"
        fi
    fi
else
    echo "   ❌ Database connection FAILED"
    echo ""
    echo "   Troubleshooting:"
    echo "   1. Check PostgreSQL is running: sudo service postgresql status"
    echo "   2. Verify credentials in .env file"
    echo "   3. Check database exists: psql -U ${DB_USER} -l"
    exit 1
fi

echo ""
echo "✅ Database connection test complete!"


