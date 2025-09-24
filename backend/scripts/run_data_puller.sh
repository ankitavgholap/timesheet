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
