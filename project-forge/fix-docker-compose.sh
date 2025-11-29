#!/bin/bash
# Fix Docker Compose connection issue

echo "🔧 Fixing Docker Compose connection..."

# Check if using Docker Desktop (WSL2)
if [ -n "$WSL_DISTRO_NAME" ]; then
    echo "📱 WSL2 detected"
    echo "   Make sure Docker Desktop is running in Windows"
    echo "   And WSL2 integration is enabled for this distro"
    echo ""
fi

# Unset problematic environment variables
unset DOCKER_HOST
unset DOCKER_TLS_VERIFY
unset DOCKER_CERT_PATH

# Test Docker connection
echo "🧪 Testing Docker connection..."
if docker ps &>/dev/null; then
    echo "✅ Docker is accessible"
else
    echo "❌ Docker is not accessible"
    echo ""
    echo "Try:"
    echo "  1. sudo service docker start"
    echo "  2. Or start Docker Desktop (Windows)"
    exit 1
fi

# Check which compose command to use
echo ""
echo "🔍 Checking Docker Compose..."
if docker compose version &>/dev/null 2>&1; then
    echo "✅ Using: docker compose (plugin)"
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    echo "⚠️  Using: docker-compose (legacy)"
    COMPOSE_CMD="docker-compose"
    
    # Test if it works
    if $COMPOSE_CMD version &>/dev/null 2>&1; then
        echo "✅ docker-compose is working"
    else
        echo "❌ docker-compose has connection issues"
        echo ""
        echo "Solution: Install Docker Compose plugin"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y docker-compose-plugin"
        exit 1
    fi
else
    echo "❌ Docker Compose not found"
    echo ""
    echo "Install with:"
    echo "  sudo apt-get install -y docker-compose-plugin"
    exit 1
fi

echo ""
echo "✅ Ready to use: $COMPOSE_CMD"
echo ""
echo "Try running:"
echo "  $COMPOSE_CMD up -d"

