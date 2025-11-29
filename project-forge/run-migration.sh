#!/bin/bash
# Script to run the database migration for strategy_type column
# This must be run as postgres superuser or a user with ALTER TABLE privileges

echo "Running database migration: add strategy_type column..."
echo ""

# Try to detect database connection details
DB_NAME="${DB_NAME:-aurora_db}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Run the migration
if command -v psql &> /dev/null; then
    echo "Using psql command line tool..."
    PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f backend/migrations/add_strategy_type.sql
else
    echo "psql not found. Please run manually:"
    echo "  psql -U postgres -d $DB_NAME -f backend/migrations/add_strategy_type.sql"
    echo ""
    echo "Or if using docker:"
    echo "  docker-compose exec db psql -U postgres -d $DB_NAME -f /tmp/add_strategy_type.sql"
    echo "  (after copying the file into the container)"
fi

