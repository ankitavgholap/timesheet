#!/bin/bash

# ActivityWatch Sync Script - Mac/Linux Version
# No additional software installation required!

# CHANGE THESE VALUES:
DEVELOPER_NAME="riddhidhakhara"
API_TOKEN="AWToken_vKeY5pcMmyvUkfh_GJh8JMHVQWhy2GYTnwxNuw2NhLI"

# Don't change below this line
SERVER_URL="http://api-timesheet.firsteconomy.com/api/sync"
LOCAL_AW="http://localhost:5600/api/0"

# Function to send data
send_data() {
    echo "Checking ActivityWatch at $(date '+%H:%M:%S')"
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        echo "Error: curl is required but not installed"
        return 1
    fi
    
    # Get ActivityWatch buckets
    buckets_response=$(curl -s --max-time 10 "$LOCAL_AW/buckets" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$buckets_response" ]; then
        echo "ActivityWatch not responding"
        return 1
    fi
    
    # Extract bucket names (simple JSON parsing)
    bucket_names=$(echo "$buckets_response" | grep -o '"[^"]*"' | head -20 | tr -d '"')
    bucket_count=$(echo "$bucket_names" | wc -l)
    echo "Found $bucket_count ActivityWatch buckets"
    
    # Calculate time range (6 minutes ago to now)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac OS
        start_time=$(date -u -v-6M '+%Y-%m-%dT%H:%M:%S.000Z')
        end_time=$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')
    else
        # Linux
        start_time=$(date -u -d '6 minutes ago' '+%Y-%m-%dT%H:%M:%S.000Z')
        end_time=$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')
    fi
    
    # Collect events from first bucket with data (FIXED)
    all_events=""
    
    for bucket in $bucket_names; do
        if [ -n "$bucket" ]; then
            events_url="$LOCAL_AW/buckets/$bucket/events?start=$start_time&end=$end_time"
            events=$(curl -s --max-time 15 "$events_url" 2>/dev/null)
            
            # Use first bucket that has valid events
            if [ $? -eq 0 ] && [ "$events" != "[]" ] && [ -n "$events" ]; then
                all_events="$events"
                echo "Using events from bucket: $bucket"
                break
            fi
        fi
    done
    
    # If no events found, use empty array
    if [ -z "$all_events" ]; then
        all_events="[]"
    fi
    
    # Check if we have any events
    if [ "$all_events" = "[]" ]; then
        echo "No new data to sync"
        return 0
    fi
    
    # Create payload
    payload="{\"name\":\"$DEVELOPER_NAME\",\"token\":\"$API_TOKEN\",\"data\":$all_events,\"timestamp\":\"$end_time\"}"
    
    # Send to server
    response=$(curl -s --max-time 20 \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$SERVER_URL" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        if echo "$response" | grep -q '"success":true'; then
            event_count=$(echo "$all_events" | grep -o '{' | wc -l)
            echo "✓ Synced $event_count events successfully"
        else
            echo "✗ Server error: $response"
        fi
    else
        echo "✗ Failed to connect to server"
    fi
}

# Main execution
echo "=================================================="
echo "ActivityWatch Sync for $DEVELOPER_NAME"
echo "=================================================="
echo "Press Ctrl+C to stop"
echo ""

# Continuous sync loop
while true; do
    send_data
    next_sync=$(date -d '+5 minutes' '+%H:%M:%S' 2>/dev/null || date -v+5M '+%H:%M:%S' 2>/dev/null || echo "in 5 minutes")
    echo "Waiting 5 minutes... (next sync at $next_sync)"
    sleep 300  # 5 minutes
done