#!/bin/bash
# setup_automated_puller.sh
# Setup script for automated ActivityWatch data pulling

echo "🚀 Setting up Automated ActivityWatch Data Puller"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Create necessary directories
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/scripts"

# Set permissions
chmod +x "$PROJECT_DIR/automated_data_puller.py"

# Create environment file if it doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "📝 Creating .env file..."
    cat > "$PROJECT_DIR/.env" << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:asdf1234@localhost:5432/timesheet

# ActivityWatch Configuration  
ACTIVITYWATCH_PORT=5600
DATA_PULL_WINDOW_MINUTES=1

# Logging
LOG_LEVEL=INFO
EOF
    echo "✅ Created .env file - please update with your actual database credentials"
fi

# Create wrapper script for cron
cat > "$PROJECT_DIR/scripts/run_data_puller.sh" << 'EOF'
#!/bin/bash
# Wrapper script for cron job execution

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)

# Change to project directory
cd "$PROJECT_DIR"

# Run the data puller
python3 "$PROJECT_DIR/automated_data_puller.py" >> "$PROJECT_DIR/logs/cron.log" 2>&1

# Log completion
echo "$(date): Data pull completed" >> "$PROJECT_DIR/logs/cron.log"
EOF

chmod +x "$PROJECT_DIR/scripts/run_data_puller.sh"

# Create log rotation script
cat > "$PROJECT_DIR/scripts/rotate_logs.sh" << 'EOF'
#!/bin/bash
# Log rotation script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"

# Rotate main log file
if [ -f "$LOG_DIR/cron.log" ]; then
    if [ $(stat -c%s "$LOG_DIR/cron.log") -gt 10485760 ]; then  # 10MB
        mv "$LOG_DIR/cron.log" "$LOG_DIR/cron.log.$(date +%Y%m%d%H%M%S)"
        touch "$LOG_DIR/cron.log"
    fi
fi

# Clean old log files (keep only last 5)
cd "$LOG_DIR" && ls -t cron.log.* | tail -n +6 | xargs -r rm

# Clean system log
if [ -f "/tmp/activitywatch_puller.log" ]; then
    if [ $(stat -c%s "/tmp/activitywatch_puller.log") -gt 10485760 ]; then  # 10MB
        mv "/tmp/activitywatch_puller.log" "/tmp/activitywatch_puller.log.$(date +%Y%m%d%H%M%S)"
        touch "/tmp/activitywatch_puller.log"
    fi
fi
EOF

chmod +x "$PROJECT_DIR/scripts/rotate_logs.sh"

# Test the data puller
echo "🧪 Testing data puller..."
python3 "$PROJECT_DIR/automated_data_puller.py"

if [ $? -eq 0 ]; then
    echo "✅ Data puller test successful"
else
    echo "❌ Data puller test failed - check configuration"
    exit 1
fi

# Setup cron job - Windows/Git Bash compatible
echo "⏰ Setting up scheduled task..."

# For Windows (using Task Scheduler), create a batch file
cat > "$PROJECT_DIR/start_data_puller.bat" << EOF
@echo off
cd /d "$PROJECT_DIR"
python automated_data_puller.py >> logs/cron.log 2>&1
EOF

# Create monitoring script
cat > "$PROJECT_DIR/scripts/monitor_puller.sh" << 'EOF'
#!/bin/bash
# Monitoring script for data puller

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📊 ActivityWatch Data Puller Status"
echo "=================================="

# Check recent log entries
echo ""
echo "📝 Recent Activity (last 10 lines):"
if [ -f "$PROJECT_DIR/logs/cron.log" ]; then
    tail -10 "$PROJECT_DIR/logs/cron.log"
else
    echo "No log file found"
fi

# Check system log
echo ""
echo "🔍 System Log (last 5 lines):"
if [ -f "/tmp/activitywatch_puller.log" ]; then
    tail -5 "/tmp/activitywatch_puller.log"
else
    echo "No system log file found"
fi

# Database check
echo ""
echo "💾 Database Status:"
python3 -c "
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('$PROJECT_DIR/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM activity_records WHERE created_at > NOW() - INTERVAL \\'5 minutes\\''))
        count = result.scalar()
        print(f'✅ Recent activities (last 5 min): {count}')
        
        result = conn.execute(text('SELECT COUNT(DISTINCT developer_id) FROM developers WHERE active = true'))
        dev_count = result.scalar()
        print(f'✅ Active developers: {dev_count}')
except Exception as e:
    print(f'❌ Database error: {e}')
"
EOF

chmod +x "$PROJECT_DIR/scripts/monitor_puller.sh"

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📁 Files created:"
echo "  - automated_data_puller.py (main data puller)"
echo "  - scripts/run_data_puller.sh (bash wrapper)"
echo "  - start_data_puller.bat (Windows batch file)"
echo "  - scripts/rotate_logs.sh (log rotation)"
echo "  - scripts/monitor_puller.sh (monitoring)"
echo "  - .env (configuration)"
echo ""
echo "🔧 For Windows/Git Bash:"
echo "  1. Update .env with your database credentials"
echo "  2. Test manually: python automated_data_puller.py"
echo "  3. Run every 10 seconds: Use Windows Task Scheduler with start_data_puller.bat"
echo "  4. Monitor: ./scripts/monitor_puller.sh"
echo ""
echo "⏰ To set up automatic running every 10 seconds:"
echo "   Option 1: Use Windows Task Scheduler (recommended for Windows)"
echo "   Option 2: Run in background: while true; do python automated_data_puller.py; sleep 10; done"
echo ""
echo "📊 Check logs in: logs/cron.log and /tmp/activitywatch_puller.log"
