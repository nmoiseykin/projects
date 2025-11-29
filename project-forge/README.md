# Project Forge (Кузница)

**The self-testing mechanical trading lab that pairs with Project Aurora.**

A web application where you describe a trading idea in plain English, the system generates backtest scenarios, executes them against your local Postgres historical dataset, and returns dashboards + AI-interpreted conclusions + concrete "what to do" strategy summaries.

## Tech Stack

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + recharts
- **Backend:** FastAPI (Python) + SQLAlchemy + Psycopg2 + Pydantic
- **Database:** PostgreSQL (local)
- **AI:** OpenAI API (GPT-4-Turbo / GPT-4o-mini)
- **Container:** Docker Compose

## Quick Start

```bash
# Development
cp .env.example .env
docker-compose up -d db
cd backend && uvicorn app.main:app --reload
cd frontend && npm i && npm run dev

# Open http://localhost:3000
# API at http://localhost:8000
```

## Project Structure

```
project-forge/
  backend/          # FastAPI backend
  frontend/         # Next.js frontend
  docs/             # Documentation
  docker-compose.yml
  .env.example
```

## Features

- 🤖 AI-powered scenario generation from natural language
- 📊 Comprehensive backtest execution engine
- 📈 Interactive dashboards with charts
- 📝 AI-generated strategy explanations
- 🔴 Live log tail via WebSocket
- 🎨 Mr. Robot themed UI

## Documentation

See `/docs` for detailed documentation:
- `PRD.md` - Product requirements
- `stack.md` - Tech stack details
- `repo-structure.md` - Repository layout
- `db.md` - Database schema
- `acceptance.md` - Acceptance criteria
