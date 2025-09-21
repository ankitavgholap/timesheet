#!/bin/bash
# Setup script for ActivityWatch Sync Client on Linux/Mac

echo "🚀 Setting up ActivityWatch Sync Client..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if ActivityWatch is running
if ! curl -s http://localhost:5600/api/0/buckets/ > /dev/null; then
    echo "⚠️  ActivityWatch doesn't seem to be running on localhost:5600"
    echo "Please start ActivityWatch before running the sync client"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    cp .env.template .env
    echo "📝 Created .env file from template"
    echo "⚠️  Please edit .env file with your server details and credentials"
else
    echo "ℹ️  .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your server URL and credentials"
echo "2. Test connection: python activitywatch_sync.py --test"
echo "3. Run sync: python activitywatch_sync.py --continuous"
echo ""
echo "Or to run as a service:"
echo "  ./install_service.sh"
