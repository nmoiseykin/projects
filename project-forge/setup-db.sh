#!/bin/bash
# Setup database tables

echo "🗄️  Setting up database tables..."
echo ""

cd ~/projects/project-forge/backend

# Check if venv exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run init script
echo "🔧 Creating database tables..."
python3 init_db.py

echo ""
echo "✅ Database setup complete!"
echo ""
echo "Now try executing your backtest again."
