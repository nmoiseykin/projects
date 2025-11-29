#!/bin/bash
# Project Forge - Stop Script

cd ~/projects/project-forge

# Determine which compose file to use
if [ -f docker-compose.localdb.yml ] && grep -q "DB_HOST=localhost" .env 2>/dev/null; then
    COMPOSE_FILE="docker-compose.localdb.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

# Check which compose command works
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found!"
    exit 1
fi

# Check if we need sudo
if ! docker ps &> /dev/null; then
    COMPOSE_CMD="sudo $COMPOSE_CMD"
fi

echo "🛑 Stopping Project Forge services..."
$COMPOSE_CMD -f "$COMPOSE_FILE" down

echo "✅ Services stopped"


