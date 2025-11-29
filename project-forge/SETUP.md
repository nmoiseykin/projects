# Project Forge - Setup Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- PostgreSQL 14+ (or use Docker)
- OpenAI API key (for AI features)

## 🌐 WSL2 Users

**If you're using WSL2** (Windows Subsystem for Linux):
- Docker runs inside WSL2
- Access from Windows browser using `localhost`
- WSL2 automatically forwards ports to Windows
- See `WSL2_SETUP.md` for detailed instructions

## Quick Start

### 1. Clone and Configure

```bash
cd ~/projects/project-forge
cp .env.example .env
```

Edit `.env` with your settings:
- Database credentials
- OpenAI API key
- API key for authentication

### 2. Database Setup

Ensure your PostgreSQL database has the `market.ohlcv_data` table:

```sql
CREATE SCHEMA IF NOT EXISTS market;

CREATE TABLE market.ohlcv_data (
    timestamp TIMESTAMP NOT NULL,
    timeframe TEXT NOT NULL,
    open_price NUMERIC NOT NULL,
    high_price NUMERIC NOT NULL,
    low_price NUMERIC NOT NULL,
    close_price NUMERIC NOT NULL,
    volume NUMERIC,
    PRIMARY KEY (timestamp, timeframe)
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_tf_ts 
ON market.ohlcv_data(timeframe, timestamp);
```

### 3. Run with Docker

```bash
docker-compose up -d db
docker-compose up api web
```

Or run services individually:

```bash
# Database only
docker-compose up -d db

# Backend (from backend directory)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (from frontend directory)
cd frontend
npm install
npm run dev
```

### 4. Access

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Database Migrations

Create Alembic migration for application tables:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests (when added)
cd frontend
npm test
```

## Troubleshooting

### Database Connection Issues

- Verify database is running: `docker-compose ps`
- Check connection string in `.env`
- Ensure database exists and user has permissions

### API Key Issues

- Set `API_KEY` in `.env`
- Include `X-API-KEY` header in requests
- Check API logs for authentication errors

### OpenAI API Issues

- Verify `OPENAI_API_KEY` is set in `.env`
- Check API quota and billing
- AI features will be disabled if key is missing

## Next Steps

1. Populate `market.ohlcv_data` with historical data
2. Create your first backtest scenario
3. Review results and AI explanations
4. Iterate on strategies

