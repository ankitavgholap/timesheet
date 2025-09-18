#!/usr/bin/env python3
"""
Direct test to match ActivityWatch UI exactly
"""
import requests
from datetime import datetime, timezone
import json

def direct_activitywatch_test():
    """Test ActivityWatch API directly with different approaches"""
    base_url = "http://localhost:5600/api/0"
    
    print("🔍 DIRECT ACTIVITYWATCH API TEST")
    print("=" * 50)
    
    try:
        # Test 1: Get all buckets and their info
        print("📊 Step 1: Getting all buckets...")
        buckets_response = requests.get(f"{base_url}/buckets")
        buckets = buckets_response.json()
        
        for bucket_name, bucket_info in buckets.items():
            print(f"   🗂️ {bucket_name}")
            print(f"      Type: {bucket_info.get('type')}")
            print(f"      Client: {bucket_info.get('client')}")
            print(f"      Created: {bucket_info.get('created')}")
        
        # Test 2: Try different date ranges around September 5th
        test_dates = [
            ("Sep 5, 2024", "2024-09-05T00:00:00", "2024-09-05T23:59:59"),
            ("Sep 1-15, 2024", "2024-09-01T00:00:00", "2024-09-15T23:59:59"),
            ("Sep 5, 2025", "2025-09-05T00:00:00", "2025-09-05T23:59:59"),
            ("Sep 1-15, 2025", "2025-09-01T00:00:00", "2025-09-15T23:59:59"),
            ("All 2024", "2024-01-01T00:00:00", "2024-12-31T23:59:59"),
            ("All 2025", "2025-01-01T00:00:00", "2025-12-31T23:59:59"),
        ]
        
        for date_name, start_str, end_str in test_dates:
            print(f"\n📅 Step 2: Testing {date_name} ({start_str} to {end_str})")
            
            for bucket_name in buckets.keys():
                if 'afk' in bucket_name.lower():
                    continue
                
                try:
                    # Try with different limits and no limit
                    for limit in [10, 100, 1000, None]:
                        params = {
                            'start': start_str,
                            'end': end_str
                        }
                        if limit:
                            params['limit'] = limit
                        
                        events_response = requests.get(
                            f"{base_url}/buckets/{bucket_name}/events",
                            params=params
                        )
                        
                        if events_response.status_code == 200:
                            events = events_response.json()
                            if events:
                                print(f"   ✅ {bucket_name} (limit={limit}): {len(events)} events")
                                
                                # Show events that match your screenshot
                                matching_events = []
                                for event in events:
                                    data = event.get('data', {})
                                    title = data.get('title', '').lower()
                                    
                                    # Look for the specific terms from your screenshot
                                    search_terms = ['waaree', 'ajax-contact', 'salesforce', 'validation', 'istana', 'kiki', 'terminus']
                                    if any(term in title for term in search_terms):
                                        matching_events.append(event)
                                
                                if matching_events:
                                    print(f"      🎯 Found {len(matching_events)} matching events:")
                                    for event in matching_events[:5]:
                                        data = event.get('data', {})
                                        title = data.get('title', '')
                                        duration = event.get('duration', 0)
                                        timestamp = event.get('timestamp', '')
                                        print(f"         • {title[:60]} ({duration:.1f}s) - {timestamp[:19]}")
                                
                                # Show first few events regardless
                                print(f"      📋 First 3 events:")
                                for i, event in enumerate(events[:3]):
                                    data = event.get('data', {})
                                    title = data.get('title', '')
                                    duration = event.get('duration', 0)
                                    timestamp = event.get('timestamp', '')
                                    print(f"         {i+1}. {title[:60]} ({duration:.1f}s) - {timestamp[:19]}")
                                
                                break  # Found data, no need to try other limits
                        else:
                            print(f"   ❌ {bucket_name} (limit={limit}): HTTP {events_response.status_code}")
                    
                except Exception as e:
                    print(f"   ❌ {bucket_name}: Error - {e}")
        
        # Test 3: Try the query endpoint (if available)
        print(f"\n📊 Step 3: Trying query endpoint...")
        try:
            query_response = requests.post(
                f"{base_url}/query",
                json={
                    "timeperiods": [["2024-09-01T00:00:00", "2024-09-15T23:59:59"]],
                    "query": [
                        "RETURN = query_bucket(find_bucket('aw-watcher-window_'));",
                        "RETURN = filter_keyvals(RETURN, 'title', []);",
                        "RETURN = sort_by_duration(RETURN);"
                    ]
                }
            )
            
            if query_response.status_code == 200:
                query_result = query_response.json()
                print(f"   ✅ Query endpoint returned: {len(query_result)} results")
                
                for i, result in enumerate(query_result[:5]):
                    data = result.get('data', {})
                    title = data.get('title', '')
                    duration = result.get('duration', 0)
                    print(f"      {i+1}. {title[:60]} ({duration:.1f}s)")
            else:
                print(f"   ❌ Query endpoint: HTTP {query_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Query endpoint error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    direct_activitywatch_test()
