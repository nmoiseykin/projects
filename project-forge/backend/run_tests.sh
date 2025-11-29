#!/bin/bash
# Quick script to run iFVG detector tests

echo "Running iFVG Detector Unit Tests..."
echo ""

cd "$(dirname "$0")"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set PYTHONPATH to current directory for imports
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "Error: pytest not found. Installing..."
    pip install pytest pytest-cov
fi

# Run tests
python -m pytest tests/test_ifvg_detector.py -v --tb=short

# Optionally run with coverage
if [ "$1" == "--coverage" ]; then
    echo ""
    echo "Running with coverage report..."
    python -m pytest tests/test_ifvg_detector.py --cov=app.services.fvg_detector --cov-report=term-missing --cov-report=html
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
fi

