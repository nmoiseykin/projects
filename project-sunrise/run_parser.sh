#!/bin/bash
# Simple script to run the ForexFactory USD calendar parser

cd "$(dirname "$0")"

echo "🚀 Starting ForexFactory USD Calendar Parser..."
echo "================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run the parser (filtering for today only)
PYTHONPATH=$(pwd):$PYTHONPATH python3 examples/parse_forexfactory_final.py --today-only

echo ""
echo "================================================"
echo "✅ Done! Check forex_calendar_usd.json in the examples/ directory"

