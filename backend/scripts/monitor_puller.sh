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
