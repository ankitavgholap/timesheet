#!/bin/bash

# ActivityWatch Sync Script - Mac/Linux Version
# No additional software installation required!

# Get developer name and token from:
# 1. Command line arguments
# 2. Environment variables
# 3. Config file
# 4. Interactive prompt

if [ -n "$1" ] && [ -n "$2" ]; then
    # From command line arguments
    DEVELOPER_NAME="$1"
    API_TOKEN="$2"
elif [ -n "$AW_DEVELOPER_NAME" ] && [ -n "$AW_API_TOKEN" ]; then
    # From environment variables
    DEVELOPER_NAME="$AW_DEVELOPER_NAME"
    API_TOKEN="$AW_API_TOKEN"
elif [ -f "$HOME/.aw-sync-config" ]; then
    # From config file
    source "$HOME/.aw-sync-config"
else
    # Interactive prompt
    echo "ActivityWatch Sync Setup"
    echo "========================"
    read -p "Enter your developer name: " DEVELOPER_NAME
    read -p "Enter your API token: " API_TOKEN
    
    # Offer to save for next time
    read -p "Save credentials for future use? (y/n): " save_config
    if [ "$save_config" = "y" ] || [ "$save_config" = "Y" ]; then
        echo "DEVELOPER_NAME=\"$DEVELOPER_NAME\"" > "$HOME/.aw-sync-config"
        echo "API_TOKEN=\"$API_TOKEN\"" >> "$HOME/.aw-sync-config"
        chmod 600 "$HOME/.aw-sync-config"
        echo "Credentials saved to ~/.aw-sync-config"
    fi
fi

# Validate inputs
if [ -z "$DEVELOPER_NAME" ] || [ -z "$API_TOKEN" ]; then
    echo "Error: Developer name and API token are required!"
    echo "Usage: $0 <developer_name> <api_token>"
    echo "Or set AW_DEVELOPER_NAME and AW_API_TOKEN environment variables"
    exit 1
fi

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
    
    # Collect events from first bucket with data (FIXED JSON HANDLING)
    all_events=""
    
    for bucket in $bucket_names; do
        if [ -n "$bucket" ] && [ -z "$all_events" ]; then
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