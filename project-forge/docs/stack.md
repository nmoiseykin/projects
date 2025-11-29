# Tech Stack

## Frontend
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Charts:** Recharts
- **Real-time:** WebSocket for logs
- **Theme:** Mr. Robot (dark, green matrixy accents)

## Backend
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLAlchemy 2.0+
- **Database Driver:** Psycopg2 (async)
- **Validation:** Pydantic v2
- **Background Jobs:** asyncio tasks (Celery optional for scale)
- **WebSocket:** FastAPI WebSocket support
- **Templating:** Jinja2 (for SQL templates)

## Database
- **Engine:** PostgreSQL 14+
- **Connection:** SQLAlchemy async engine
- **Migrations:** Alembic

## AI
- **Provider:** OpenAI API
- **Models:**
  - Reasoning/Code/Analysis: **GPT-4-Turbo** (or GPT-4.1 if enabled)
  - Fast sweeps: **GPT-4o-mini**

## Authentication
- **Dev:** Simple API key header (`X-API-KEY`)
- **Prod:** Add proper auth later (JWT, OAuth, etc.)

## Container
- **Orchestration:** Docker Compose
- **Services:** web, api, db

## Observability
- **Logging:** Structured JSON logs to file + console
- **App Log:** `APP_LOG_FILE` (default: `./logs/app.log`)
- **Live Tail:** WebSocket streaming at `/ws/logs`



