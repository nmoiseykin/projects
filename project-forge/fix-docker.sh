#!/bin/bash
# Quick fix for Docker connection issues

echo "🔧 Fixing Docker connection..."

# Check if Docker Desktop is running (via WSL2)
if [ -n "$WSL_DISTRO_NAME" ]; then
    echo "📱 WSL2 detected"
    echo "   If using Docker Desktop, make sure it's running in Windows"
    echo "   And WSL2 integration is enabled"
fi

# Try to start Docker service
echo ""
echo "🚀 Starting Docker service..."
if sudo service docker start 2>/dev/null; then
    echo "✅ Docker service started"
    sleep 2
else
    echo "⚠️  Could not start Docker service"
    echo "   You may need Docker Desktop or manual Docker installation"
fi

# Check Docker socket
echo ""
echo "🔍 Checking Docker socket..."
if [ -S /var/run/docker.sock ]; then
    echo "✅ Docker socket exists"
    ls -l /var/run/docker.sock
else
    echo "❌ Docker socket not found"
fi

# Test Docker connection
echo ""
echo "🧪 Testing Docker connection..."
if docker ps &>/dev/null; then
    echo "✅ Docker is working!"
    docker ps
else
    echo "❌ Docker still not working"
    echo ""
    echo "Try these:"
    echo "  1. sudo usermod -aG docker \$USER"
    echo "  2. newgrp docker"
    echo "  3. Or use Docker Desktop with WSL2 integration"
fi
