#!/bin/bash
# Setup database tables with proper permissions

echo "🗄️  Setting up database tables..."
echo ""

cd ~/projects/project-forge

echo "This script will create the database tables."
echo "You may be prompted for your sudo password."
echo ""

# Try to run as postgres user
if sudo -u postgres psql -d aurora_db -f create-tables.sql; then
    echo ""
    echo "✅ Database tables created successfully!"
    echo ""
    echo "Verifying tables..."
    PGPASSWORD=aurora_pass123 psql -h localhost -U aurora_user -d aurora_db -c "\dt backtest_*"
else
    echo ""
    echo "❌ Failed to create tables automatically."
    echo ""
    echo "Please run manually:"
    echo "  sudo -u postgres psql -d aurora_db -f create-tables.sql"
    echo ""
    echo "Or connect to PostgreSQL and run the SQL commands:"
    echo "  sudo -u postgres psql -d aurora_db"
    echo "  Then paste the contents of create-tables.sql"
fi


