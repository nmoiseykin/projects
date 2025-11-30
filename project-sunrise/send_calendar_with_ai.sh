#!/bin/bash
# Complete workflow: Fetch calendar, get AI analysis, and send email

cd "$(dirname "$0")"

echo "🚀 ForexFactory Calendar + AI Analysis - Complete Workflow"
echo "============================================================"
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
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
OPENAI_ASSISTANT_ID="${OPENAI_ASSISTANT_ID:-}"

# Check if required config is provided
if [ -z "$TO_EMAIL" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo "⚠️  Email configuration required!"
    echo ""
    echo "Please set environment variables:"
    echo "  export TO_EMAIL='recipient@example.com'"
    echo "  export SMTP_USER='your_email@gmail.com'"
    echo "  export SMTP_PASSWORD='your_app_password'"
    echo "  export OPENAI_API_KEY='sk-...'"
    echo "  export OPENAI_ASSISTANT_ID='asst_...'"
    echo ""
    exit 1
fi

# Step 1: Fetch and parse calendar (today only)
echo "📊 Step 1: Fetching ForexFactory calendar (TODAY only)..."
PYTHONPATH=$(pwd):$PYTHONPATH python3 examples/parse_forexfactory_final.py \
    --today-only \
    --output examples/forex_calendar_usd.json

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch calendar"
    exit 1
fi

echo ""

# Step 2: Get AI analysis (if configured)
AI_ANALYSIS_ARG=""
if [ -n "$OPENAI_API_KEY" ] && [ -n "$OPENAI_ASSISTANT_ID" ]; then
    echo "🤖 Step 2: Getting AI market analysis..."
    python3 examples/openai_assistant.py \
        --assistant-id "$OPENAI_ASSISTANT_ID" \
        --api-key "$OPENAI_API_KEY" \
        --questions-file examples/questions.txt \
        --calendar-json examples/forex_calendar_usd.json \
        --output examples/ai_analysis.json
    
    if [ $? -eq 0 ]; then
        echo "✅ AI analysis completed"
        AI_ANALYSIS_ARG="--ai-analysis examples/ai_analysis.json"
    else
        echo "⚠️  AI analysis failed, continuing without it..."
    fi
else
    echo "⏭️  Step 2: Skipping AI analysis (not configured)"
    echo "   Set OPENAI_API_KEY and OPENAI_ASSISTANT_ID to enable"
fi

echo ""
echo "📧 Step 3: Sending email..."

# Step 3: Send email
PYTHONPATH=$(pwd):$PYTHONPATH python3 examples/send_calendar_email.py \
    --json-file examples/forex_calendar_usd.json \
    $AI_ANALYSIS_ARG \
    --to-email "$TO_EMAIL" \
    --smtp-user "$SMTP_USER" \
    --smtp-password "$SMTP_PASSWORD"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ Complete! Calendar with AI analysis sent to $TO_EMAIL"
    echo "============================================================"
else
    echo "❌ Failed to send email"
    exit 1
fi

