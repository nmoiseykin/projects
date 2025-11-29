# Docker and .env File Explanation

## 📁 .env File Location

### Location
The `.env` file should be in the **root of the project**:
```
~/projects/project-forge/.env
```

### Purpose
The `.env` file stores environment variables (configuration) that your application needs:
- Database credentials
- API keys (OpenAI, etc.)
- Application settings
- Security keys

### How to Create It

1. **Copy the example file:**
   ```bash
   cd ~/projects/project-forge
   cp .env.example .env
   ```

2. **Edit `.env` with your actual values:**
   ```bash
   nano .env
   # or
   vim .env
   ```

3. **Important:** Never commit `.env` to git (it's in `.gitignore`)

### Example .env File
```bash
# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=project_forge_db
DB_USER=myuser
DB_PASSWORD=mypassword

# OpenAI API
OPENAI_API_KEY=sk-your-actual-key-here

# Application Settings
APP_ENV=dev
APP_LOG_FILE=./logs/app.log
APP_PORT=8000
TZ_DB_SOURCE=America/Chicago
TZ_TRADING=America/New_York

# API Security
API_KEY=my-secure-api-key-12345
```

---

## 🐳 Docker Purpose

### What is Docker?
Docker is a containerization platform that packages your application and its dependencies into isolated containers.

### Why Use Docker in This Project?

#### 1. **Consistency**
- Same environment on every machine (dev, staging, production)
- No "works on my machine" problems
- Dependencies are locked in containers

#### 2. **Easy Setup**
Instead of manually installing:
- PostgreSQL
- Python 3.11 with all packages
- Node.js 18 with npm packages
- Configuring everything

You just run:
```bash
docker-compose up
```

#### 3. **Isolation**
- Each service (database, API, frontend) runs in its own container
- No conflicts with other projects on your machine
- Easy to clean up (just stop containers)

#### 4. **Development Workflow**

**With Docker:**
```bash
# Start everything
docker-compose up

# Stop everything
docker-compose down

# View logs
docker-compose logs -f api
```

**Without Docker:**
```bash
# Install PostgreSQL
sudo apt-get install postgresql

# Install Python packages
pip install -r requirements.txt

# Install Node packages
npm install

# Configure database
# Set up environment variables
# Start each service manually
# ... many more steps
```

### Docker Services in This Project

#### 1. **Database Service (`db`)**
```yaml
db:
  image: postgres:14
  ports:
    - "5432:5432"
```
- Runs PostgreSQL 14 in a container
- Accessible on `localhost:5432`
- Data persists in a Docker volume

#### 2. **API Service (`api`)**
```yaml
api:
  build: ./backend
  ports:
    - "8000:8000"
```
- Runs FastAPI backend
- Accessible on `localhost:8000`
- Hot-reloads code changes (volume mount)

#### 3. **Web Service (`web`)**
```yaml
web:
  build: ./frontend
  ports:
    - "3000:3000"
```
- Runs Next.js frontend
- Accessible on `localhost:3000`
- Hot-reloads code changes

### Docker Compose Benefits

1. **Orchestration**: Starts all services together
2. **Networking**: Services can talk to each other (`api` → `db`)
3. **Dependencies**: `api` waits for `db` to be healthy
4. **Volumes**: Code changes reflect immediately (development)

### How Docker Reads .env

Docker Compose automatically reads `.env` from the project root:
```yaml
environment:
  DB_HOST: ${DB_HOST}  # Reads from .env file
  DB_PASSWORD: ${DB_PASSWORD}
```

### Development vs Production

**Development (with Docker):**
```bash
docker-compose up
# All services start automatically
# Code changes hot-reload
```

**Development (without Docker):**
```bash
# Terminal 1: Start database
postgres

# Terminal 2: Start backend
cd backend && uvicorn app.main:app --reload

# Terminal 3: Start frontend
cd frontend && npm run dev
```

**Production (with Docker):**
```bash
docker-compose -f docker-compose.prod.yml up -d
# Runs optimized production builds
```

---

## 📋 Quick Reference

### .env File
- **Location**: `~/projects/project-forge/.env`
- **Purpose**: Store configuration (database, API keys)
- **Security**: Never commit to git

### Docker
- **Purpose**: Run all services in isolated containers
- **Command**: `docker-compose up`
- **Benefits**: Easy setup, consistency, isolation

### Common Commands
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build

# Access database
docker-compose exec db psql -U your_user -d your_db
```

---

## 🎯 Summary

- **`.env` file**: Configuration file in project root (`~/projects/project-forge/.env`)
- **Docker**: Containerization platform that runs all services (database, API, frontend) together
- **Why Docker**: Makes setup easy, ensures consistency, isolates services


