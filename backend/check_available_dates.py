#!/usr/bin/env python3
"""
Check what date ranges actually have data in ActivityWatch
"""
import requests
from datetime import datetime, timedelta, timezone

def check_available_dates():
    """Check what dates have data in ActivityWatch"""
    base_url = "http://localhost:5600/api/0"
    
    try:
        print("🔍 CHECKING AVAILABLE DATA DATES IN ACTIVITYWATCH")
        print("=" * 60)
        
        # Get buckets
        buckets_response = requests.get(f"{base_url}/buckets")
        buckets = buckets_response.json()
        
        print(f"📊 Available buckets: {list(buckets.keys())}")
        
        # Check different date ranges
        date_ranges = [
            ("Last 24 hours", datetime.now(timezone.utc) - timedelta(days=1), datetime.now(timezone.utc)),
            ("Last 7 days", datetime.now(timezone.utc) - timedelta(days=7), datetime.now(timezone.utc)),
            ("Last 30 days", datetime.now(timezone.utc) - timedelta(days=30), datetime.now(timezone.utc)),
            ("Sep 1-15, 2024", datetime(2024, 9, 1, tzinfo=timezone.utc), datetime(2024, 9, 15, tzinfo=timezone.utc)),
            ("Sep 1-15, 2025", datetime(2025, 9, 1, tzinfo=timezone.utc), datetime(2025, 9, 15, tzinfo=timezone.utc)),
            ("All of 2024", datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 12, 31, tzinfo=timezone.utc)),
            ("All of 2025", datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, tzinfo=timezone.utc)),
        ]
        
        for range_name, start, end in date_ranges:
            print(f"\n📅 Checking {range_name} ({start.date()} to {end.date()}):")
            
            total_events = 0
            for bucket_name in buckets.keys():
                if 'afk' in bucket_name.lower():
                    continue
                    
                try:
                    start_str = start.strftime('%Y-%m-%dT%H:%M:%S')
                    end_str = end.strftime('%Y-%m-%dT%H:%M:%S')
                    
                    events_response = requests.get(
                        f"{base_url}/buckets/{bucket_name}/events",
                        params={
                            'start': start_str,
                            'end': end_str,
                            'limit': 100
                        }
                    )
                    
                    if events_response.status_code == 200:
                        events = events_response.json()
                        bucket_events = len(events)
                        total_events += bucket_events
                        
                        if bucket_events > 0:
                            print(f"   {bucket_name}: {bucket_events} events")
                            
                            # Show first few events to see what dates they have
                            for i, event in enumerate(events[:3]):
                                timestamp = event.get('timestamp', '')
                                data = event.get('data', {})
                                title = data.get('title', '')[:50]
                                duration = event.get('duration', 0)
                                print(f"     {i+1}. {timestamp[:19]} | {title} ({duration:.1f}s)")
                        else:
                            print(f"   {bucket_name}: 0 events")
                    else:
                        print(f"   {bucket_name}: Error {events_response.status_code}")
                        
                except Exception as e:
                    print(f"   {bucket_name}: Error - {e}")
            
            print(f"   📊 Total events in {range_name}: {total_events}")
        
        # Also check the bucket info to see when data starts/ends
        print(f"\n📊 BUCKET INFORMATION:")
        print("-" * 40)
        
        for bucket_name, bucket_info in buckets.items():
            if 'afk' in bucket_name.lower():
                continue
                
            print(f"\n🗂️ {bucket_name}:")
            print(f"   Type: {bucket_info.get('type', 'Unknown')}")
            print(f"   Client: {bucket_info.get('client', 'Unknown')}")
            print(f"   Hostname: {bucket_info.get('hostname', 'Unknown')}")
            print(f"   Created: {bucket_info.get('created', 'Unknown')}")
            
            # Try to get the earliest and latest events
            try:
                # Get earliest events
                early_response = requests.get(
                    f"{base_url}/buckets/{bucket_name}/events",
                    params={'limit': 1, 'start': '2020-01-01T00:00:00', 'end': '2030-12-31T23:59:59'}
                )
                
                if early_response.status_code == 200:
                    early_events = early_response.json()
                    if early_events:
                        earliest = early_events[0].get('timestamp', 'Unknown')
                        print(f"   Earliest event: {earliest}")
                
                # Get latest events  
                late_response = requests.get(
                    f"{base_url}/buckets/{bucket_name}/events",
                    params={'limit': 1, 'start': '2020-01-01T00:00:00', 'end': '2030-12-31T23:59:59', 'order': 'desc'}
                )
                
                if late_response.status_code == 200:
                    late_events = late_response.json()
                    if late_events:
                        latest = late_events[0].get('timestamp', 'Unknown')
                        print(f"   Latest event: {latest}")
                        
            except Exception as e:
                print(f"   Error getting date range: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_available_dates()
