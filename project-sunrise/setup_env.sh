#!/bin/bash
# Interactive script to create .env file

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║  📝 Environment Configuration Setup                      ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists!"
    echo ""
    read -p "Overwrite existing .env file? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "❌ Cancelled. Existing .env file kept."
        exit 0
    fi
    # Backup existing .env
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✓ Backed up existing .env file"
    echo ""
fi

echo "Please provide your configuration:"
echo "══════════════════════════════════════════════════════════"
echo ""

# Email Configuration
echo "📧 EMAIL CONFIGURATION (Required)"
echo "──────────────────────────────────────────────────────────"
read -p "Recipient Email: " TO_EMAIL
read -p "SMTP User (Gmail): " SMTP_USER
read -sp "SMTP Password (App Password): " SMTP_PASSWORD
echo ""
echo ""

# OpenAI Configuration
echo "🤖 OPENAI CONFIGURATION (Optional - press Enter to skip)"
echo "──────────────────────────────────────────────────────────"
read -p "OpenAI API Key (or press Enter): " OPENAI_API_KEY
read -p "OpenAI Assistant ID (or press Enter): " OPENAI_ASSISTANT_ID
echo ""

# Validate required fields
if [ -z "$TO_EMAIL" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo "❌ Error: Email configuration is required!"
    exit 1
fi

# Create .env file
echo "Creating .env file..."
cat > .env << EOF
# ForexFactory Calendar Email Configuration
# Generated on $(date)
# DO NOT commit this file to git!

# Email Configuration
TO_EMAIL=$TO_EMAIL
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD

# OpenAI Configuration
OPENAI_API_KEY=$OPENAI_API_KEY
OPENAI_ASSISTANT_ID=$OPENAI_ASSISTANT_ID

# Advanced Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
LOG_FILE=/tmp/forex_calendar.log
EOF

# Secure the file (only owner can read/write)
chmod 600 .env

echo ""
echo "══════════════════════════════════════════════════════════"
echo "✅ SUCCESS! .env file created"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "File location: $(pwd)/.env"
echo "Permissions: 600 (owner read/write only)"
echo ""
echo "Configuration summary:"
echo "  📧 Email: $TO_EMAIL"
echo "  👤 SMTP User: $SMTP_USER"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "  🤖 AI: Enabled"
else
    echo "  🤖 AI: Disabled (not configured)"
fi
echo ""
echo "Next steps:"
echo "  1. Test the configuration:"
echo "     ./send_calendar_with_ai.sh"
echo ""
echo "  2. Set up daily schedule:"
echo "     ./setup_daily_schedule.sh"
echo ""
echo "  3. Or manually add to crontab:"
echo "     crontab -e"
echo "     Add: 0 7 * * * cd $(pwd) && ./send_calendar_with_ai.sh"
echo ""
echo "══════════════════════════════════════════════════════════"

