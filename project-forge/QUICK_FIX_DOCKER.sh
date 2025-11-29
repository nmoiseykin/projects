#!/bin/bash
# Quick fix for Docker connection error

echo "🔧 Fixing Docker Connection..."
echo ""

# Option 1: Try to start Docker service
echo "1️⃣  Attempting to start Docker service..."
if sudo service docker start 2>/dev/null; then
    echo "   ✅ Docker service started"
    sleep 2
else
    echo "   ⚠️  Could not start Docker service (may need password)"
    echo ""
    echo "   Please run manually:"
    echo "   sudo service docker start"
fi

# Option 2: Check if Docker Desktop is needed
echo ""
echo "2️⃣  Checking for Docker Desktop..."
if [ -n "$WSL_DISTRO_NAME" ]; then
    echo "   📱 WSL2 detected"
    echo ""
    echo "   💡 RECOMMENDED: Use Docker Desktop for Windows"
    echo "   1. Open Docker Desktop in Windows"
    echo "   2. Settings → Resources → WSL Integration"
    echo "   3. Enable your WSL2 distro"
    echo "   4. Apply & Restart"
    echo ""
fi

# Option 3: Fix permissions
echo "3️⃣  Checking Docker permissions..."
if [ -S /var/run/docker.sock ]; then
    echo "   ✅ Docker socket exists"
    if ! docker ps &>/dev/null; then
        echo "   ⚠️  Permission issue detected"
        echo ""
        echo "   Please run:"
        echo "   sudo usermod -aG docker \$USER"
        echo "   newgrp docker"
    fi
else
    echo "   ❌ Docker socket not found"
fi

# Test
echo ""
echo "4️⃣  Testing Docker..."
if docker ps &>/dev/null; then
    echo "   ✅ Docker is working!"
    docker ps
else
    echo "   ❌ Docker still not working"
    echo ""
    echo "   📝 Manual steps:"
    echo "   1. sudo service docker start"
    echo "   2. sudo usermod -aG docker \$USER"
    echo "   3. newgrp docker"
    echo "   4. docker ps"
fi


