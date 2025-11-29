# Repository Structure

```
project-forge/
  backend/
    app/
      main.py               # FastAPI app & routes
      api/
        routes_backtest.py  # POST /backtests, GET /backtests/:id, GET /backtests/:id/results
        routes_ai.py         # POST /ai/suggest, POST /ai/explain
        routes_logs.py       # GET /logs/tail (sse) or /ws/logs (websocket)
      core/
        config.py           # env, settings
        db.py               # engine, session, alembic setup
        logging.py          # uvicorn + app logger
      services/
        scenarios.py        # grid builder + AI-driven parameter expansion
        runner.py           # orchestrates SQL execution (async)
        sql_templates.py    # parameterized SQL Jinja2 templates
        analyzer.py         # KPIs: win%, expectancy, PF, timeouts, etc.
        ai.py               # OpenAI prompts for suggest/explain
        tz.py               # helpers for CST->NY
        results.py          # persistence helpers
      models/
        backtest.py         # pydantic schemas
        orm.py              # SQLAlchemy models for results & runs
      sql/
        base_templates/
          by_year.sql.j2
          by_candle.sql.j2
          by_dow.sql.j2
    tests/
      test_sql_templates.py
      test_runner.py
    requirements.txt
    Dockerfile
  frontend/
    app/
      layout.tsx
      page.tsx              # dashboard
      chat/page.tsx
      scenarios/page.tsx
      results/[runId]/page.tsx
      logs/page.tsx
    components/
      Shell.tsx
      Chat.tsx
      ScenarioForm.tsx
      ResultsTable.tsx
      KPI.tsx
      ChartWinRate.tsx
      LogTail.tsx
    lib/
      api.ts
      theme.css             # mr. robot theme tokens
    package.json
    tsconfig.json
    tailwind.config.js
    Dockerfile
  docker-compose.yml
  .env.example
  README.md
  docs/
    PRD.md
    stack.md
    repo-structure.md
    db.md
    acceptance.md
```



