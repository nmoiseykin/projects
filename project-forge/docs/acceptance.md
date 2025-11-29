# Acceptance Criteria

## Core Functionality

1. **Natural Language to Scenarios**
   - ✅ User types: "test 9:45 bearish → 9:50 short/long, 60/30, to 12:00, years 2020–2025, 1m+5m group by year and DoW"
   - ✅ AI returns 10 scenarios
   - ✅ Clicking "Run" creates a run_id and executes scenarios

2. **Live Log Streaming**
   - ✅ `/logs` shows live log tail while run is executing
   - ✅ WebSocket connection maintains stable connection
   - ✅ Logs appear in real-time with proper formatting

3. **Results Display**
   - ✅ `/results/{run_id}` shows results tables
   - ✅ Charts render correctly (by year, DoW, candle)
   - ✅ Data is accurate and matches SQL output

4. **AI Strategy Explanation**
   - ✅ Clicking "Explain with AI" produces markdown strategy brief
   - ✅ Brief includes "what to do" bullet points
   - ✅ Brief includes risks and checklist

5. **SQL Template Accuracy**
   - ✅ SQL templates **always** convert CST→NY
   - ✅ Column names match database schema exactly
   - ✅ Parameters are safely injected (no SQL injection)

6. **Security**
   - ✅ API requires `X-API-KEY` header (configurable)
   - ✅ Invalid keys return 401
   - ✅ Keys can be configured via environment

7. **Deployment**
   - ✅ All configuration in `.env`
   - ✅ App boots via `docker-compose up`
   - ✅ Database migrations run automatically

## Performance

- ✅ Single run with 100+ scenarios completes in < 5 minutes
- ✅ WebSocket maintains connection under load
- ✅ UI remains responsive during execution

## Testing

- ✅ Unit tests for template rendering
- ✅ Integration test with small date slice
- ✅ Load test with 100+ scenarios
- ✅ WebSocket streaming test under load
- ✅ UI smoke tests for all pages



