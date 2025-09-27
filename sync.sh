# Collect events from all buckets
all_events=""

for bucket in $bucket_names; do
    if [ -n "$bucket" ]; then
        events_url="$LOCAL_AW/buckets/$bucket/events?start=$start_time&end=$end_time"
        
        # Get events and save to temp file to preserve JSON
        curl -s --max-time 15 "$events_url" -o /tmp/aw_events_temp.json 2>/dev/null
        
        if [ $? -eq 0 ] && [ -s /tmp/aw_events_temp.json ]; then
            # Check if file contains actual events (not just [])
            if ! grep -q '^\[\]$' /tmp/aw_events_temp.json; then
                # Use the events directly without modification
                all_events=$(cat /tmp/aw_events_temp.json)
                echo "Using events from bucket: $bucket"
                break
            fi
        fi
    fi
done

# Clean up temp file
rm -f /tmp/aw_events_temp.json

# If no events found, use empty array
if [ -z "$all_events" ]; then
    all_events="[]"
fi