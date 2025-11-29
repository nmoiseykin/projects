# Quick Start - Run Project Forge

## 🚀 Start the Project

Since you have existing PostgreSQL, use this command:

```bash
cd ~/projects/project-forge

# Start API and Web (skip Docker database)
docker-compose -f docker-compose.localdb.yml up -d
```

Or if you have Docker permissions fixed:

```bash
# Start all services (including Docker database)
docker-compose up -d
```

## 🌐 Access URLs

Once services are running, access from your **Windows browser**:

- **Frontend (Web UI)**: http://localhost:3000
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📊 Check Status

```bash
# Check if services are running
docker-compose ps

# Or with localdb config
docker-compose -f docker-compose.localdb.yml ps
```

## 📝 View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
docker-compose logs -f web
```

## 🛑 Stop Services

```bash
# Stop all services
docker-compose down

# Or with localdb config
docker-compose -f docker-compose.localdb.yml down
```

## ⚠️ If You Get Permission Errors

```bash
# Add user to docker group (run once)
sudo usermod -aG docker $USER

# Apply changes
newgrp docker

# Then try again
docker-compose up -d
```

## 🔧 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs
```

### Can't connect to database
- Make sure your PostgreSQL is running
- Check DB credentials in `.env` file
- Verify PostgreSQL is accessible on port 5432

### Port already in use
- Check if something else is using ports 3000 or 8000
- Stop conflicting services or change ports in docker-compose.yml
