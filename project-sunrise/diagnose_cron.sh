#!/bin/bash
# Diagnostic script to troubleshoot cron job issues

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║  🔍 Cron Job Diagnostic Tool                            ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "Running diagnostics..."
echo ""

# 1. Check if cron service is running
echo "═══════════════════════════════════════════════════════════"
echo "1. Checking cron service status"
echo "═══════════════════════════════════════════════════════════"
if systemctl is-active --quiet cron 2>/dev/null || systemctl is-active --quiet crond 2>/dev/null; then
    pass "Cron service is running"
elif pgrep -x "cron" > /dev/null || pgrep -x "crond" > /dev/null; then
    pass "Cron daemon is running"
else
    fail "Cron service is NOT running!"
    echo "   Try: sudo systemctl start cron"
    echo "   Or:  sudo systemctl start crond"
fi
echo ""

# 2. Check if crontab exists
echo "═══════════════════════════════════════════════════════════"
echo "2. Checking user crontab"
echo "═══════════════════════════════════════════════════════════"
if crontab -l > /dev/null 2>&1; then
    pass "User crontab exists"
    echo ""
    echo "Current crontab entries:"
    echo "───────────────────────────────────────────────────────────"
    crontab -l | grep -v "^#" | grep -v "^$" || echo "(no active entries)"
    echo "───────────────────────────────────────────────────────────"
else
    fail "No crontab for current user"
    echo "   Run: ./setup_daily_schedule.sh"
fi
echo ""

# 3. Check script permissions
echo "═══════════════════════════════════════════════════════════"
echo "3. Checking script permissions"
echo "═══════════════════════════════════════════════════════════"
SCRIPTS=("run_parser.sh" "send_calendar.sh" "send_calendar_with_ai.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            pass "$script is executable"
        else
            fail "$script is NOT executable"
            echo "   Fix: chmod +x $script"
        fi
    else
        warn "$script not found"
    fi
done
echo ""

# 4. Check log file
echo "═══════════════════════════════════════════════════════════"
echo "4. Checking log file"
echo "═══════════════════════════════════════════════════════════"
LOG_FILE="/tmp/forex_calendar.log"
if [ -f "$LOG_FILE" ]; then
    pass "Log file exists: $LOG_FILE"
    SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
    echo "   Size: $SIZE bytes"
    echo ""
    echo "Last 10 lines of log:"
    echo "───────────────────────────────────────────────────────────"
    tail -10 "$LOG_FILE"
    echo "───────────────────────────────────────────────────────────"
else
    warn "Log file not found: $LOG_FILE"
    echo "   This might mean the cron job never ran"
fi
echo ""

# 5. Check today's execution
echo "═══════════════════════════════════════════════════════════"
echo "5. Checking if job ran today"
echo "═══════════════════════════════════════════════════════════"
TODAY=$(date +%Y-%m-%d)
if [ -f "$LOG_FILE" ]; then
    if grep -q "$TODAY" "$LOG_FILE"; then
        pass "Job ran today ($TODAY)"
        echo ""
        echo "Today's log entries:"
        echo "───────────────────────────────────────────────────────────"
        grep "$TODAY" "$LOG_FILE" | tail -20
        echo "───────────────────────────────────────────────────────────"
    else
        fail "No entries for today ($TODAY) in log"
    fi
else
    fail "Cannot check - log file doesn't exist"
fi
echo ""

# 6. Check system cron logs
echo "═══════════════════════════════════════════════════════════"
echo "6. Checking system cron logs"
echo "═══════════════════════════════════════════════════════════"
if [ -f "/var/log/syslog" ]; then
    CRON_ENTRIES=$(grep CRON /var/log/syslog | grep "$(whoami)" | tail -5)
    if [ -n "$CRON_ENTRIES" ]; then
        pass "Found cron executions in syslog"
        echo "$CRON_ENTRIES"
    else
        warn "No recent cron executions found for user $(whoami)"
    fi
elif [ -f "/var/log/cron" ]; then
    CRON_ENTRIES=$(grep "$(whoami)" /var/log/cron | tail -5)
    if [ -n "$CRON_ENTRIES" ]; then
        pass "Found cron executions in cron log"
        echo "$CRON_ENTRIES"
    else
        warn "No recent cron executions found for user $(whoami)"
    fi
else
    warn "Cannot access system cron logs"
    echo "   Try: sudo grep CRON /var/log/syslog | tail -20"
fi
echo ""

# 7. Test script manually
echo "═══════════════════════════════════════════════════════════"
echo "7. Testing manual execution"
echo "═══════════════════════════════════════════════════════════"
echo "Would you like to test the script manually now? (y/n)"
read -r RESPONSE

if [ "$RESPONSE" = "y" ] || [ "$RESPONSE" = "Y" ]; then
    echo ""
    echo "Testing send_calendar_with_ai.sh..."
    echo "───────────────────────────────────────────────────────────"
    
    # Check if environment variables are set
    if [ -z "$TO_EMAIL" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
        echo ""
        echo "Environment variables not set. Please provide:"
        read -p "TO_EMAIL: " TO_EMAIL
        read -p "SMTP_USER: " SMTP_USER
        read -sp "SMTP_PASSWORD: " SMTP_PASSWORD
        echo ""
        read -p "OPENAI_API_KEY (or press Enter to skip): " OPENAI_API_KEY
        read -p "OPENAI_ASSISTANT_ID (or press Enter to skip): " OPENAI_ASSISTANT_ID
        
        export TO_EMAIL SMTP_USER SMTP_PASSWORD OPENAI_API_KEY OPENAI_ASSISTANT_ID
    fi
    
    ./send_calendar_with_ai.sh
    
    echo ""
    echo "───────────────────────────────────────────────────────────"
    if [ $? -eq 0 ]; then
        pass "Script executed successfully!"
    else
        fail "Script failed to execute"
    fi
fi
echo ""

# 8. Common issues and solutions
echo "═══════════════════════════════════════════════════════════"
echo "8. Common Issues & Solutions"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "ISSUE: Cron service not running"
echo "  FIX: sudo systemctl start cron"
echo "       sudo systemctl enable cron"
echo ""
echo "ISSUE: Environment variables not set in cron"
echo "  FIX: Make sure all exports are in the cron line"
echo "       Or source a config file before running script"
echo ""
echo "ISSUE: Wrong timezone"
echo "  FIX: Check timezone with: timedatectl"
echo "       Cron uses system time"
echo ""
echo "ISSUE: Script not executable"
echo "  FIX: chmod +x send_calendar_with_ai.sh"
echo ""
echo "ISSUE: Path issues in cron"
echo "  FIX: Use full paths: /home/nmoiseykin/webpage-parser/..."
echo ""
echo "ISSUE: Python virtual environment not activated"
echo "  FIX: Scripts automatically activate venv"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Review the diagnostics above"
echo "  2. Check 'crontab -l' to verify schedule"
echo "  3. Test manual run: ./send_calendar_with_ai.sh"
echo "  4. Check logs after 7 AM tomorrow"
echo "  5. Read SCHEDULING_GUIDE.md for details"
echo ""
echo "═══════════════════════════════════════════════════════════"

