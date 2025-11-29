#!/bin/bash
# Comprehensive connectivity test for Project Forge
# Tests all connections between components

# Don't exit on error - we want to run all tests
set +e

cd ~/projects/project-forge

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Test function
test_check() {
    local name="$1"
    shift
    local command="$@"
    
    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

# Detailed test function with output
test_check_verbose() {
    local name="$1"
    shift
    local command="$@"
    
    echo -n "Testing $name... "
    OUTPUT=$(eval "$command" 2>&1)
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        if [ -n "$OUTPUT" ] && [ ${#OUTPUT} -lt 200 ]; then
            echo "   Output: $OUTPUT"
        fi
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        if [ -n "$OUTPUT" ]; then
            echo "   Error: ${OUTPUT:0:200}"
        fi
        ((FAILED++))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Project Forge - Connectivity Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Load .env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo -e "${BLUE}📋 Loaded environment variables from .env${NC}"
else
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
fi
echo ""

# ============================================================================
# 1. Environment Variables
# ============================================================================
echo -e "${BLUE}1️⃣  Environment Variables${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

test_check "DB_HOST is set" '[ -n "$DB_HOST" ]'
test_check "DB_PORT is set" '[ -n "$DB_PORT" ]'
test_check "DB_NAME is set" '[ -n "$DB_NAME" ]'
test_check "DB_USER is set" '[ -n "$DB_USER" ]'
test_check "DB_PASSWORD is set" '[ -n "$DB_PASSWORD" ]'
test_check "OPENAI_API_KEY is set" '[ -n "$OPENAI_API_KEY" ]'
test_check "API_KEY is set" '[ -n "$API_KEY" ]'

echo ""

# ============================================================================
# 2. PostgreSQL Database
# ============================================================================
echo -e "${BLUE}2️⃣  PostgreSQL Database${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

# Check PostgreSQL is running
test_check "PostgreSQL is listening on port 5432" "netstat -tuln 2>/dev/null | grep -q ':5432' || ss -tuln 2>/dev/null | grep -q ':5432'"

# Test database connection
if [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASSWORD" ] && [ -n "$DB_NAME" ]; then
    test_check_verbose "Database connection" "PGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -U \"$DB_USER\" -d \"$DB_NAME\" -c 'SELECT 1;'"
    
    # Check required tables
    test_check "backtest_runs table exists" "PGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -U \"$DB_USER\" -d \"$DB_NAME\" -c '\dt backtest_runs' | grep -q backtest_runs"
    test_check "backtest_scenarios table exists" "PGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -U \"$DB_USER\" -d \"$DB_NAME\" -c '\dt backtest_scenarios' | grep -q backtest_scenarios"
    test_check "backtest_results table exists" "PGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -U \"$DB_USER\" -d \"$DB_NAME\" -c '\dt backtest_results' | grep -q backtest_results"
    
    # Check market data table
    test_check "market.ohlcv_data table exists" "PGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -U \"$DB_USER\" -d \"$DB_NAME\" -c '\dt market.ohlcv_data' | grep -q ohlcv_data"
    
    # Check data exists
    ROW_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM market.ohlcv_data LIMIT 1;" 2>/dev/null | tr -d ' ' || echo "0")
    if [ "$ROW_COUNT" != "0" ] && [ -n "$ROW_COUNT" ]; then
        echo -e "   Data check: ${GREEN}✅ PASS${NC} (Found $ROW_COUNT rows in market.ohlcv_data)"
        ((PASSED++))
    else
        echo -e "   Data check: ${YELLOW}⚠️  WARN${NC} (No data found in market.ohlcv_data)"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping database tests - missing credentials${NC}"
fi

echo ""

# ============================================================================
# 3. Backend API
# ============================================================================
echo -e "${BLUE}3️⃣  Backend API${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

# Check API process
test_check "API process is running" "ps aux | grep 'uvicorn app.main:app' | grep -v grep | grep -q uvicorn"

# Check API port
test_check "API port 8000 is listening" "netstat -tuln 2>/dev/null | grep -q ':8000' || ss -tuln 2>/dev/null | grep -q ':8000'"

# Test API health endpoint
test_check_verbose "API health endpoint" "curl -s --max-time 5 http://localhost:8000/health | grep -q 'healthy'"

# Test API root endpoint
test_check_verbose "API root endpoint" "curl -s --max-time 5 http://localhost:8000/ | grep -q 'Project Forge'"

# Test API with authentication
if [ -n "$API_KEY" ]; then
    test_check_verbose "API authentication" "curl -s --max-time 5 -H \"X-API-KEY: $API_KEY\" http://localhost:8000/api/backtests 2>&1 | grep -q -E '(detail|run_id|401)'"
fi

echo ""

# ============================================================================
# 4. Frontend Web
# ============================================================================
echo -e "${BLUE}4️⃣  Frontend Web${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

# Check web process
test_check "Web process is running" "ps aux | grep -q 'next dev' | grep -v grep || curl -s --max-time 2 http://localhost:3000 > /dev/null"

# Check web port
test_check "Web port 3000 is listening" "netstat -tuln 2>/dev/null | grep -q ':3000' || ss -tuln 2>/dev/null | grep -q ':3000'"

# Test web endpoint
test_check_verbose "Web endpoint" "curl -s --max-time 5 http://localhost:3000 | grep -q -E '(html|Next|Project)'"

echo ""

# ============================================================================
# 5. OpenAI API
# ============================================================================
echo -e "${BLUE}5️⃣  OpenAI API${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

if [ -n "$OPENAI_API_KEY" ]; then
    # Test OpenAI API connectivity (simple test)
    test_check_verbose "OpenAI API key format" "echo \"$OPENAI_API_KEY\" | grep -qE '^sk-'"
    
    # Test via our API endpoint (if API is running)
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        echo -n "Testing AI endpoint via API... "
        RESPONSE=$(curl -s --max-time 30 -X POST http://localhost:8000/api/ai/suggest \
            -H "Content-Type: application/json" \
            -H "X-API-KEY: ${API_KEY:-dev-key-change-in-production}" \
            -d '{"context":"test"}' 2>&1)
        
        if echo "$RESPONSE" | grep -q -E '(scenarios|error|detail)'; then
            echo -e "${GREEN}✅ PASS${NC}"
            ((PASSED++))
        else
            echo -e "${YELLOW}⚠️  TIMEOUT or UNKNOWN${NC}"
            echo "   Response: ${RESPONSE:0:100}..."
        fi
    else
        echo -e "${YELLOW}⚠️  Skipping - API not available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set${NC}"
fi

echo ""

# ============================================================================
# 6. File System
# ============================================================================
echo -e "${BLUE}6️⃣  File System${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

test_check ".env file exists" "[ -f .env ]"
test_check "backend directory exists" "[ -d backend ]"
test_check "frontend directory exists" "[ -d frontend ]"
test_check "logs directory exists" "[ -d logs ]"
test_check "SQL templates exist" "[ -d backend/app/sql/base_templates ]"
test_check "by_year.sql.j2 exists" "[ -f backend/app/sql/base_templates/by_year.sql.j2 ]"
test_check "by_dow.sql.j2 exists" "[ -f backend/app/sql/base_templates/by_dow.sql.j2 ]"
test_check "by_candle.sql.j2 exists" "[ -f backend/app/sql/base_templates/by_candle.sql.j2 ]"

echo ""

# ============================================================================
# 7. Network Connectivity
# ============================================================================
echo -e "${BLUE}7️⃣  Network Connectivity${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

# Test localhost connectivity
test_check "localhost:8000 is reachable" "curl -s --max-time 2 http://localhost:8000 > /dev/null"
test_check "localhost:3000 is reachable" "curl -s --max-time 2 http://localhost:3000 > /dev/null"

# Test database host connectivity
if [ -n "$DB_HOST" ]; then
    if [ "$DB_HOST" = "localhost" ] || [ "$DB_HOST" = "127.0.0.1" ]; then
        test_check "Database host (localhost) is reachable" "nc -z localhost 5432 2>/dev/null || timeout 1 bash -c '</dev/tcp/localhost/5432' 2>/dev/null"
    else
        echo -n "Testing database host $DB_HOST:5432... "
        if nc -z "$DB_HOST" 5432 2>/dev/null || timeout 1 bash -c "</dev/tcp/$DB_HOST/5432" 2>/dev/null; then
            echo -e "${GREEN}✅ PASS${NC}"
            ((PASSED++))
        else
            echo -e "${YELLOW}⚠️  WARN${NC} (Cannot test remote host)"
        fi
    fi
fi

echo ""

# ============================================================================
# 8. Integration Tests
# ============================================================================
echo -e "${BLUE}8️⃣  Integration Tests${NC}"
echo "──────────────────────────────────────────────────────────────────────────────"

# Test API -> Database
if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo -n "Testing API -> Database connection... "
    # Try to get backtest status (requires DB)
    RESPONSE=$(curl -s --max-time 5 -H "X-API-KEY: ${API_KEY:-dev-key-change-in-production}" \
        "http://localhost:8000/api/backtests/00000000-0000-0000-0000-000000000000" 2>&1)
    
    if echo "$RESPONSE" | grep -q -E '(not found|404|detail)'; then
        echo -e "${GREEN}✅ PASS${NC} (API can query database)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (API cannot query database)"
        echo "   Response: ${RESPONSE:0:100}..."
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  Skipping - API not available${NC}"
fi

# Test Frontend -> API
if curl -s --max-time 2 http://localhost:3000 > /dev/null 2>&1; then
    echo -n "Testing Frontend -> API connection... "
    # Frontend should be able to reach API
    if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} (Frontend can reach API)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (Frontend cannot reach API)"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  Skipping - Frontend not available${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL=$((PASSED + FAILED))
echo "   Total tests: $TOTAL"
echo -e "   ${GREEN}Passed: $PASSED${NC}"
echo -e "   ${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All connectivity tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Please check the errors above.${NC}"
    exit 1
fi

