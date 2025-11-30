#!/bin/bash
# Setup script to schedule daily ForexFactory calendar + AI analysis at 7 AM

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║  📅 Setup Daily Schedule - 7 AM                         ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Get configuration
read -p "Recipient Email: " TO_EMAIL
read -p "SMTP User (Gmail): " SMTP_USER
read -sp "SMTP Password (App Password): " SMTP_PASSWORD
echo ""
read -p "OpenAI API Key (or press Enter to skip): " OPENAI_API_KEY
read -p "OpenAI Assistant ID (or press Enter to skip): " OPENAI_ASSISTANT_ID
echo ""

# Determine which script to use
if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_ASSISTANT_ID" ]; then
    SCRIPT="send_calendar_with_ai.sh"
    echo "✓ Will use AI-enhanced workflow"
else
    SCRIPT="send_calendar.sh"
    echo "✓ Will use standard workflow (no AI)"
fi

# Get project path
PROJECT_PATH="/home/nmoiseykin/webpage-parser"

# Create cron job line
CRON_LINE="0 7 * * * export TO_EMAIL='$TO_EMAIL' SMTP_USER='$SMTP_USER' SMTP_PASSWORD='$SMTP_PASSWORD'"

if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_ASSISTANT_ID" ]; then
    CRON_LINE="$CRON_LINE OPENAI_API_KEY='$OPENAI_API_KEY' OPENAI_ASSISTANT_ID='$OPENAI_ASSISTANT_ID'"
fi

CRON_LINE="$CRON_LINE && cd $PROJECT_PATH && ./$SCRIPT >> /tmp/forex_calendar.log 2>&1"

# Show what will be added
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "This cron job will be added:"
echo "═══════════════════════════════════════════════════════════"
echo "$CRON_LINE"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Schedule: Every day at 7:00 AM"
echo "Log file: /tmp/forex_calendar.log"
echo ""

read -p "Add this cron job? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "❌ Cancelled"
    exit 0
fi

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -

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
    echo "Check logs:"
    echo "  tail -f /tmp/forex_calendar.log"
    echo ""
    echo "Test run now:"
    echo "  cd $PROJECT_PATH && ./$SCRIPT"
    echo ""
    echo "Remove schedule:"
    echo "  crontab -e  (then delete the line)"
    echo ""
else
    echo "❌ Failed to add cron job"
    exit 1
fi

