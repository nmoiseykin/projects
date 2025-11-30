#!/bin/bash
# Setup cron job using .env file for configuration

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║  📅 Setup Daily Cron Job (Using .env file)              ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create .env file first:"
    echo "  ./setup_env.sh"
    echo ""
    exit 1
fi

# Load and validate .env
source .env

if [ -z "$TO_EMAIL" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo "❌ Error: Required email configuration missing in .env file!"
    echo ""
    echo "Please check your .env file has:"
    echo "  TO_EMAIL=..."
    echo "  SMTP_USER=..."
    echo "  SMTP_PASSWORD=..."
    echo ""
    exit 1
fi

# Determine which script to use
if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_ASSISTANT_ID" ]; then
    SCRIPT="send_calendar_with_ai.sh"
    echo "✓ AI-enhanced workflow will be used"
else
    SCRIPT="send_calendar.sh"
    echo "✓ Standard workflow will be used (no AI)"
fi

# Get project path
PROJECT_PATH="$(pwd)"
LOG_FILE="${LOG_FILE:-/tmp/forex_calendar.log}"

# Create cron job line
CRON_LINE="0 7 * * * cd $PROJECT_PATH && ./$SCRIPT >> $LOG_FILE 2>&1"

# Show what will be added
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "This cron job will be added:"
echo "═══════════════════════════════════════════════════════════"
echo "$CRON_LINE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Schedule: Every day at 7:00 AM"
echo "Script: $SCRIPT"
echo "Log file: $LOG_FILE"
echo "Config: Uses .env file in $PROJECT_PATH"
echo ""
echo "Note: The script will automatically load credentials from .env"
echo ""

read -p "Add this cron job? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ Cancelled"
    exit 0
fi

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Add new cron job (remove any existing forex-related jobs first)
(crontab -l 2>/dev/null | grep -v "forex\|ForexFactory\|webpage-parser/$SCRIPT" ; echo "$CRON_LINE") | crontab -

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Cron job added."
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "Your calendar will now be sent daily at 7:00 AM"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "View scheduled jobs:"
    echo "  crontab -l"
    echo ""
    echo "Test run now:"
    echo "  cd $PROJECT_PATH && ./$SCRIPT"
    echo ""
    echo "Check logs:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "Remove schedule:"
    echo "  crontab -e  (then delete the line)"
    echo ""
    echo "Configuration:"
    echo "  Edit: $PROJECT_PATH/.env"
    echo ""
else
    echo "❌ Failed to add cron job"
    exit 1
fi

