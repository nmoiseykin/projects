#!/bin/bash
# Project Forge - Fixed Start Script (bypasses Python docker-compose issues)

set -e

cd ~/projects/project-forge

echo "🚀 Project Forge - Starting Services..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Unset problematic Docker environment variables
unset DOCKER_HOST
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env with your database credentials!${NC}"
    else
        echo -e "${RED}❌ .env.example not found!${NC}"
        exit 1
    fi
fi

# Check Docker
echo "🔍 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    exit 1
fi

# Test Docker connection
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker connection issue${NC}"
    echo "   Trying to start Docker service..."
    sudo service docker start 2>/dev/null || true
    sleep 2
    
    if ! docker ps &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Docker daemon${NC}"
        echo "   Please start Docker: sudo service docker start"
        echo "   Or use Docker Desktop with WSL2 integration"
        exit 1
    fi
fi

# Determine which compose command to use
COMPOSE_CMD=""
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    echo -e "${GREEN}✅ Using: docker compose (plugin)${NC}"
elif command -v docker-compose &> /dev/null; then
    # Test if docker-compose works (bypass Python issues)
    if docker-compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
        echo -e "${YELLOW}⚠️  Using: docker-compose (legacy)${NC}"
    else
        echo -e "${RED}❌ docker-compose is broken${NC}"
        echo ""
        echo "   Installing Docker Compose plugin..."
        sudo apt-get update -qq
        sudo apt-get install -y docker-compose-plugin
        if docker compose version &> /dev/null 2>&1; then
            COMPOSE_CMD="docker compose"
            echo -e "${GREEN}✅ Installed and using: docker compose${NC}"
        else
            echo -e "${RED}❌ Failed to install docker-compose-plugin${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}❌ Docker Compose not found!${NC}"
    echo "   Installing..."
    sudo apt-get update -qq
    sudo apt-get install -y docker-compose-plugin
    COMPOSE_CMD="docker compose"
fi

echo -e "${GREEN}✅ Docker is ready${NC}"
echo ""

# Create logs directory
mkdir -p logs

# Determine compose file
USE_LOCAL_DB=false
if grep -q "DB_HOST=localhost" .env 2>/dev/null || grep -q "DB_HOST=127.0.0.1" .env 2>/dev/null; then
    USE_LOCAL_DB=true
    COMPOSE_FILE="docker-compose.localdb.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="docker-compose.yml"
fi

# Stop existing containers
echo "🛑 Stopping any existing containers..."
$COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true
echo ""

# Start services
echo "📦 Starting services with: $COMPOSE_CMD"
echo ""
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build

# Wait for services
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 8

# Check status
echo ""
echo "📊 Service Status:"
echo ""
$COMPOSE_CMD -f "$COMPOSE_FILE" ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Project Forge is UP!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access URLs:"
echo "   📱 Frontend:    http://localhost:3000"
echo "   🔌 API:         http://localhost:8000"
echo "   📚 API Docs:   http://localhost:8000/docs"
echo ""

