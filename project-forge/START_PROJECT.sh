#!/bin/bash
# Script to start Project Forge

set -e

cd ~/projects/project-forge

echo "🚀 Starting Project Forge..."
echo ""

# Check Docker
if ! docker ps &>/dev/null; then
    echo "⚠️  Docker permission issue detected"
    echo "   Trying with sudo..."
    SUDO_CMD="sudo"
else
    SUDO_CMD=""
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Creating from template..."
    cp .env.example .env
    echo "   ⚠️  Please edit .env with your settings before continuing"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start services
echo "📦 Starting Docker services..."
if command -v docker-compose &> /dev/null; then
    $SUDO_CMD docker-compose up -d
elif docker compose version &> /dev/null; then
    $SUDO_CMD docker compose up -d
else
    echo "❌ Docker Compose not found!"
    exit 1
fi

# Wait for services
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check status
echo ""
echo "📊 Service Status:"
if command -v docker-compose &> /dev/null; then
    $SUDO_CMD docker-compose ps
else
    $SUDO_CMD docker compose ps
fi

echo ""
echo "✅ Project Forge is starting!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop:      docker-compose down"


