#!/bin/bash
# Complete workflow: Fetch calendar, parse, and send email

cd "$(dirname "$0")"

echo "🚀 ForexFactory USD Calendar - Fetch & Email Workflow"
echo "========================================================"
echo ""

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📝 Loading configuration from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  Warning: .env file not found!"
    echo "   Run: ./setup_env.sh to create it"
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Configuration (use .env values, or fall back to environment variables)
TO_EMAIL="${TO_EMAIL:-}"
SMTP_USER="${SMTP_USER:-}"
SMTP_PASSWORD="${SMTP_PASSWORD:-}"

# Check if email config is provided
if [ -z "$TO_EMAIL" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo "⚠️  Email configuration required!"
    echo ""
    echo "Please set environment variables:"
    echo "  export TO_EMAIL='recipient@example.com'"
    echo "  export SMTP_USER='your_email@gmail.com'"
    echo "  export SMTP_PASSWORD='your_app_password'"
    echo ""
    echo "Or run the scripts manually with command-line arguments."
    echo "See examples/README.md for detailed instructions."
    exit 1
fi

# Step 1: Fetch and parse calendar (today only)
echo "📊 Step 1: Fetching ForexFactory calendar (TODAY only)..."
PYTHONPATH=$(pwd):$PYTHONPATH python3 examples/parse_forexfactory_final.py --today-only

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch calendar"
    exit 1
fi

echo ""
echo "📧 Step 2: Sending email..."

# Step 2: Send email
PYTHONPATH=$(pwd):$PYTHONPATH python3 examples/send_calendar_email.py \
    --json-file examples/forex_calendar_usd.json \
    --to-email "$TO_EMAIL" \
    --smtp-user "$SMTP_USER" \
    --smtp-password "$SMTP_PASSWORD"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================"
    echo "✅ Complete! Calendar sent to $TO_EMAIL"
    echo "========================================================"
else
    echo "❌ Failed to send email"
    exit 1
fi

