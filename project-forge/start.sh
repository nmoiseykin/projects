#!/bin/bash
# Project Forge - Auto Start Script
# This script will start everything for you

set -e

cd ~/projects/project-forge

# Deactivate any active venv (docker-compose needs system Python)
if [ -n "$VIRTUAL_ENV" ]; then
    echo "⚠️  Deactivating venv for Docker operations..."
    deactivate 2>/dev/null || true
fi

echo "🚀 Project Forge - Starting Services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env with your database credentials!${NC}"
        echo ""
    else
        echo -e "${RED}❌ .env.example not found!${NC}"
        exit 1
    fi
fi

# Check Docker
echo "🔍 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "   Please install Docker first. See INSTALLATION.md"
    exit 1
fi

# Fix Docker connection - explicitly set DOCKER_HOST to use Unix socket
# Also fix Python docker-compose issues by excluding user site-packages
export DOCKER_HOST=unix:///var/run/docker.sock
export PYTHONNOUSERSITE=1
export PYTHONPATH=""
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH

# Check Docker permissions and connection
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker connection issue detected${NC}"
    echo "   Attempting to fix..."
    
    # Try to start Docker service (if using systemd)
    if systemctl is-active --quiet docker 2>/dev/null || sudo service docker status &>/dev/null; then
        echo "   Docker service exists, trying to start..."
        sudo service docker start 2>/dev/null || true
        sleep 2
    fi
    
    # Test again
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✅ Docker is now accessible${NC}"
    else
        echo -e "${YELLOW}⚠️  Still having issues. Trying with sudo...${NC}"
        if sudo docker ps &> /dev/null; then
            DOCKER_CMD="sudo docker"
            # Prefer docker compose plugin over docker-compose
            if sudo docker compose version &> /dev/null 2>&1; then
                COMPOSE_CMD="sudo docker compose"
            else
                COMPOSE_CMD="sudo docker-compose"
            fi
        else
            echo -e "${RED}❌ Cannot connect to Docker daemon${NC}"
            echo ""
            echo "   Please try one of these:"
            echo "   1. Start Docker: sudo service docker start"
            echo "   2. Or use Docker Desktop (Windows) and enable WSL2 integration"
            echo "   3. Add user to docker group: sudo usermod -aG docker \$USER"
            echo "      Then run: newgrp docker"
            exit 1
        fi
    fi
fi

# Set Docker commands (prefer new docker compose over old docker-compose)
if [ -z "$DOCKER_CMD" ]; then
    DOCKER_CMD="docker"
    # Prefer docker compose (plugin) over docker-compose (Python package)
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        echo -e "${GREEN}✅ Using Docker Compose plugin${NC}"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo -e "${YELLOW}⚠️  Using legacy docker-compose${NC}"
        # Environment variables already set above (PYTHONNOUSERSITE, PYTHONPATH, DOCKER_HOST)
    else
        echo -e "${RED}❌ Docker Compose not found!${NC}"
        echo "   Install with: sudo apt-get install docker-compose-plugin"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Docker is ready${NC}"
echo ""

# Create logs directory
mkdir -p logs
echo "📁 Logs directory ready"
echo ""

# Check if using existing PostgreSQL
USE_LOCAL_DB=false
if grep -q "DB_HOST=localhost" .env 2>/dev/null || grep -q "DB_HOST=127.0.0.1" .env 2>/dev/null; then
    USE_LOCAL_DB=true
    echo "📊 Detected: Using existing local PostgreSQL"
    COMPOSE_FILE="docker-compose.localdb.yml"
else
    echo "📊 Using: Docker PostgreSQL container"
    COMPOSE_FILE="docker-compose.yml"
fi

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${YELLOW}⚠️  $COMPOSE_FILE not found, using default${NC}"
    COMPOSE_FILE="docker-compose.yml"
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
# Ensure env vars are set for docker-compose
PYTHONNOUSERSITE=1 PYTHONPATH="" DOCKER_HOST=unix:///var/run/docker.sock $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true
echo ""

# Start services
echo "📦 Starting services with: $COMPOSE_CMD"
echo ""

# Ensure env vars are set for docker-compose commands
if [ "$COMPOSE_FILE" = "docker-compose.localdb.yml" ]; then
    PYTHONNOUSERSITE=1 PYTHONPATH="" DOCKER_HOST=unix:///var/run/docker.sock $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build
else
    PYTHONNOUSERSITE=1 PYTHONPATH="" DOCKER_HOST=unix:///var/run/docker.sock $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build
fi

# Wait for services to start
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 8

# Check service status
echo ""
echo "📊 Service Status:"
echo ""

if PYTHONNOUSERSITE=1 PYTHONPATH="" DOCKER_HOST=unix:///var/run/docker.sock $COMPOSE_CMD -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services are running!${NC}"
    echo ""
    
    # Show service details
    PYTHONNOUSERSITE=1 PYTHONPATH="" DOCKER_HOST=unix:///var/run/docker.sock $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}🎉 Project Forge is UP and RUNNING!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 Access URLs (from Windows browser):"
    echo ""
    echo "   📱 Frontend:    http://localhost:3000"
    echo "   🔌 API:         http://localhost:8000"
    echo "   📚 API Docs:   http://localhost:8000/docs"
    echo ""
    echo "📝 Useful Commands:"
    echo ""
    echo "   View logs:     $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    echo "   Stop services: $COMPOSE_CMD -f $COMPOSE_FILE down"
    echo "   Restart:       $COMPOSE_CMD -f $COMPOSE_FILE restart"
    echo ""
    
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    echo ""
    echo "📋 Checking logs..."
    PYTHONNOUSERSITE=1 PYTHONPATH="" DOCKER_HOST=unix:///var/run/docker.sock $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=50
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check Docker is running: docker ps"
    echo "   2. Check logs: $COMPOSE_CMD -f $COMPOSE_FILE logs"
    echo "   3. Verify .env file has correct database credentials"
    exit 1
fi


