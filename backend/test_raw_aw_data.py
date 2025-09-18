#!/usr/bin/env python3
"""
Test script to see raw ActivityWatch data
"""
import requests
from datetime import datetime, timedelta, timezone
import json

def test_raw_activitywatch():
    """Test raw ActivityWatch API directly"""
    base_url = "http://localhost:5600/api/0"
    
    try:
        # Get buckets
        print("🔍 TESTING RAW ACTIVITYWATCH API")
        print("=" * 50)
        
        buckets_response = requests.get(f"{base_url}/buckets")
        buckets = buckets_response.json()
        
        print(f"📊 Available buckets: {list(buckets.keys())}")
        
        # Get events from each bucket for the last 24 hours
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=24)
        
        start_str = start.strftime('%Y-%m-%dT%H:%M:%S')
        end_str = end.strftime('%Y-%m-%dT%H:%M:%S')
        
        all_events = []
        
        for bucket_name in buckets.keys():
            if 'afk' in bucket_name.lower():
                continue
                
            print(f"\n🔍 Getting events from bucket: {bucket_name}")
            
            try:
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
                    print(f"   Found {len(events)} events")
                    
                    # Show first few events
                    for i, event in enumerate(events[:5]):
                        data = event.get('data', {})
                        duration = event.get('duration', 0)
                        
                        app_name = data.get('app', data.get('application', 'Unknown'))
                        window_title = data.get('title', '')
                        
                        print(f"   {i+1}. {app_name}: {window_title[:80]} ({duration:.1f}s)")
                        
                        all_events.append({
                            'bucket': bucket_name,
                            'app': app_name,
                            'title': window_title,
                            'duration': duration,
                            'data': data
                        })
                else:
                    print(f"   Error: {events_response.status_code}")
                    
            except Exception as e:
                print(f"   Error getting events: {e}")
        
        # Group by title and show top ones
        print(f"\n🏆 TOP WINDOW TITLES (from {len(all_events)} total events):")
        print("-" * 80)
        
        title_stats = {}
        for event in all_events:
            title = event['title']
            app = event['app']
            duration = event['duration']
            
            if duration < 5:  # Skip very short activities
                continue
                
            key = f"{title}|{app}"
            if key not in title_stats:
                title_stats[key] = {
                    'title': title,
                    'app': app,
                    'total_duration': 0,
                    'count': 0
                }
            
            title_stats[key]['total_duration'] += duration
            title_stats[key]['count'] += 1
        
        # Sort and show top 20
        sorted_titles = sorted(
            title_stats.values(),
            key=lambda x: x['total_duration'],
            reverse=True
        )[:20]
        
        for i, item in enumerate(sorted_titles, 1):
            duration_min = item['total_duration'] / 60
            print(f"{i:2d}. {item['title'][:60]:<60} | {item['app']:<15} | {duration_min:6.1f}m")
        
        # Look for specific terms you mentioned
        search_terms = ['waree', 'ajax', 'salesform', 'validation', 'claude', 'chatgpt', 'kiki', 'terminus', 'istana', 'leads']
        
        print(f"\n🔍 SEARCHING FOR SPECIFIC TERMS:")
        print("-" * 50)
        
        for term in search_terms:
            matches = [
                event for event in all_events 
                if term.lower() in event['title'].lower() and event['duration'] > 5
            ]
            
            if matches:
                print(f"\n✅ Found '{term}' in {len(matches)} activities:")
                for match in matches[:3]:  # Show top 3
                    duration_min = match['duration'] / 60
                    print(f"   • {match['title'][:80]} ({duration_min:.1f}m)")
            else:
                print(f"❌ No matches found for '{term}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_raw_activitywatch()
