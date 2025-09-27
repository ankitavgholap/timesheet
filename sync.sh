#!/bin/bash

# ActivityWatch Sync Script - Mac/Linux Version
# No additional software installation required!

# Get developer details from:
# 1. Command line arguments: ./sync.sh "name" "token"
# 2. Environment variables: AW_DEVELOPER_NAME and AW_API_TOKEN
# 3. Config file: ~/.aw-sync-config

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
    read -s -p "Enter your API token: " API_TOKEN
    echo ""
    
    # Offer to save for future use
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
    echo ""
    echo "Usage options:"
    echo "  1. ./sync.sh \"developer_name\" \"api_token\""
    echo "  2. Export environment variables:"
    echo "     export AW_DEVELOPER_NAME=\"your_name\""
    echo "     export AW_API_TOKEN=\"your_token\""
    echo "  3. Create config file ~/.aw-sync-config with:"
    echo "     DEVELOPER_NAME=\"your_name\""
    echo "     API_TOKEN=\"your_token\""
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
    
    # Create temp file for payload
    TEMP_FILE="/tmp/aw_sync_payload_$$.json"
    
    # Find first bucket with events and save to temp file
    found_events=false
    
    for bucket in $bucket_names; do
        if [ -n "$bucket" ]; then
            events_url="$LOCAL_AW/buckets/$bucket/events?start=$start_time&end=$end_time"
            
            # Get events and save directly to file
            curl -s --max-time 15 "$events_url" -o "/tmp/aw_events_$$.json" 2>/dev/null
            
            if [ $? -eq 0 ] && [ -s "/tmp/aw_events_$$.json" ]; then
                # Check if file contains valid events (not empty array)
                if ! grep -q '^\[\]$' "/tmp/aw_events_$$.json"; then
                    echo "Using events from bucket: $bucket"
                    
                    # Build JSON payload using printf for proper escaping
                    printf '{"name":"%s","token":"%s","data":' "$DEVELOPER_NAME" "$API_TOKEN" > "$TEMP_FILE"
                    cat "/tmp/aw_events_$$.json" >> "$TEMP_FILE"
                    printf ',"timestamp":"%s"}' "$end_time" >> "$TEMP_FILE"
                    
                    found_events=true
                    break
                fi
            fi
        fi
    done
    
    # Clean up events temp file
    rm -f "/tmp/aw_events_$$.json"
    
    if [ "$found_events" = false ]; then
        echo "No new data to sync"
        rm -f "$TEMP_FILE"
        return 0
    fi
    
    # Send to server using the temp file
    response=$(curl -s --max-time 20 \
        -X POST \
        -H "Content-Type: application/json" \
        --data-binary "@$TEMP_FILE" \
        "$SERVER_URL" 2>/dev/null)
    
    # Count events for reporting
    event_count=$(grep -o '{' "$TEMP_FILE" | wc -l)
    
    # Clean up temp file
    rm -f "$TEMP_FILE"
    
    if [ $? -eq 0 ]; then
        if echo "$response" | grep -q '"success":true'; then
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