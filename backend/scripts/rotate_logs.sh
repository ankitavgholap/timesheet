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
