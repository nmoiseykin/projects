# Product Requirements Document: Project Forge

## Executive Summary

**Project Forge (Кузница)** — the self-testing mechanical trading lab that pairs with **Project Aurora**.

### Goal
A web app where you describe a trading idea in plain English, the system generates backtest scenarios (time windows, TP/SL, directions, timeframes), executes them against your **local Postgres** historical dataset, and returns dashboards + AI-interpreted conclusions + concrete "what to do" strategy summaries.

### Data Source
- Table: `market.ohlcv_data`
- Columns: `timestamp (CST)`, `timeframe ('1m','5m',...)`, `open_price, high_price, low_price, close_price, volume`
- **Critical:** Timestamps must be converted **America/Chicago → America/New_York** before logic

### Scope

1. **Chat Interface** - Chat with AI to "request tests"
2. **Scenario Generator** - Grid + AI-suggested parameter combinations
3. **Backtest Runner** - SQL templates + Python executor
4. **Results Store** - Persistence + dashboards
5. **Live Log Tail** - Real-time log streaming from backend
6. **Mr. Robot UI** - Themed interface (dark, green matrixy accents)
7. **Explainable Strategies** - AI writes playbook from stats

## User Stories

- **U1**: As a trader, I can generate scenarios from natural language using AI and run them.
- **U2**: As a trader, I can see per-year, per-weekday, per-candle results.
- **U3**: As a trader, I can read a plain-english strategy brief and checklist.
- **U4**: As a power user, I can watch the live log tail through the browser.
- **U5**: As a quant, I can export CSV of results for offline work.

## Acceptance Criteria

1. I can type in chat: "test 9:45 bearish → 9:50 short/long, 60/30, to 12:00, years 2020–2025, 1m+5m group by year and DoW".
   - AI returns 10 scenarios.
   - Clicking "Run" creates a run_id and executes scenarios.
2. `/logs` shows live log tail while run is executing.
3. `/results/{run_id}` shows results tables and charts.
4. Clicking "Explain with AI" produces a markdown strategy brief with **what to do** bullet points.
5. SQL templates **always** convert CST→NY and match column names.
6. Security: API requires `X-API-KEY` header (configurable).
7. All env in `.env`; app boots via `docker-compose up`.



