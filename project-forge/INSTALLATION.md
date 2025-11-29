# Installation Guide - Project Forge

Complete guide to install all dependencies for Project Forge on WSL2.

## 📋 Prerequisites Checklist

- [ ] WSL2 installed and running
- [ ] Docker installed in WSL2
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Git installed

---

## 🐳 Step 1: Install Docker in WSL2

### Option A: Docker Desktop (Recommended for Windows)

1. **Install Docker Desktop for Windows:**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Install and run Docker Desktop
   - Enable WSL2 integration in Docker Desktop settings

2. **Verify Docker is working:**
   ```bash
   docker --version
   docker-compose --version
   ```

### Option B: Docker Engine in WSL2 (Alternative)

If you prefer Docker Engine directly in WSL2:

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
```

---

## 🐍 Step 2: Install Python 3.11+

```bash
# Check current Python version
python3 --version

# If Python 3.11+ is not installed, install it:
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Verify installation
python3.11 --version
pip3 --version
```

---

## 📦 Step 3: Install Node.js 18+

### Option A: Using NodeSource (Recommended)

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### Option B: Using nvm (Node Version Manager)

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload shell
source ~/.bashrc

# Install Node.js 18
nvm install 18
nvm use 18

# Verify installation
node --version
npm --version
```

---

## 🔧 Step 4: Install Project Dependencies

### Backend Dependencies (Python)

```bash
cd ~/projects/project-forge/backend

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

### Frontend Dependencies (Node.js)

```bash
cd ~/projects/project-forge/frontend

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

---

## ⚙️ Step 5: Configure Environment

```bash
cd ~/projects/project-forge

# Create .env file from template
cp .env.example .env

# Edit .env with your settings
nano .env
# or
vim .env
```

**Required settings in `.env`:**
- Database credentials (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
- OpenAI API key (OPENAI_API_KEY)
- API key for authentication (API_KEY)

---

## ✅ Step 6: Verify Installation

### Check Docker

```bash
# Test Docker
docker run hello-world

# Check Docker Compose
docker-compose --version
```

### Check Python

```bash
# Activate virtual environment
cd ~/projects/project-forge/backend
source venv/bin/activate

# Test Python imports
python3 -c "import fastapi; print('FastAPI OK')"
python3 -c "import sqlalchemy; print('SQLAlchemy OK')"
```

### Check Node.js

```bash
cd ~/projects/project-forge/frontend

# Test Node.js
node --version

# Test npm packages
npm list next react
```

---

## 🚀 Step 7: Start Services

### Option A: Using Docker (Recommended)

```bash
cd ~/projects/project-forge

# Start all services
docker-compose up

# Or start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option B: Manual Start (Development)

**Terminal 1 - Database:**
```bash
# If using Docker for database only
docker-compose up db

# Or if you have PostgreSQL installed locally
# (configure in .env)
```

**Terminal 2 - Backend:**
```bash
cd ~/projects/project-forge/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 3 - Frontend:**
```bash
cd ~/projects/project-forge/frontend
npm run dev
```

---

## 🔍 Troubleshooting

### Docker Issues

**Problem: "Cannot connect to Docker daemon"**
```bash
# Start Docker service
sudo service docker start

# Or if using Docker Desktop, make sure it's running in Windows
```

**Problem: "Permission denied"**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Python Issues

**Problem: "pip: command not found"**
```bash
sudo apt-get install python3-pip
```

**Problem: "Module not found"**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Node.js Issues

**Problem: "npm: command not found"**
```bash
# Reinstall Node.js (see Step 3)
```

**Problem: "EACCES: permission denied"**
```bash
# Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

---

## 📝 Quick Reference

### Install Everything (One Command)

```bash
# Docker (if using Docker Engine)
sudo apt-get update && sudo apt-get install -y docker.io docker-compose

# Python
sudo apt-get install -y python3.11 python3-pip python3-venv

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs

# Project dependencies
cd ~/projects/project-forge/backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ~/projects/project-forge/frontend && npm install
```

### Verify Everything

```bash
# Check versions
docker --version
docker-compose --version
python3 --version
node --version
npm --version

# Check project dependencies
cd ~/projects/project-forge/backend && source venv/bin/activate && pip list
cd ~/projects/project-forge/frontend && npm list --depth=0
```

---

## 🎯 Summary

1. **Install Docker** (Docker Desktop or Docker Engine)
2. **Install Python 3.11+** (`sudo apt-get install python3.11`)
3. **Install Node.js 18+** (NodeSource or nvm)
4. **Install backend dependencies** (`pip install -r requirements.txt`)
5. **Install frontend dependencies** (`npm install`)
6. **Configure .env** (`cp .env.example .env`)
7. **Start services** (`docker-compose up`)

---

## 📚 Additional Resources

- Docker Docs: https://docs.docker.com/
- Python Docs: https://docs.python.org/3/
- Node.js Docs: https://nodejs.org/docs/
- WSL2 Setup: See `WSL2_SETUP.md`


