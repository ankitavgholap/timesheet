#!/usr/bin/env python3
"""
Debug script to see what window titles are being captured
"""
from activitywatch_client import ActivityWatchClient
from datetime import datetime, timedelta, timezone

def debug_window_titles():
    """Debug window titles being captured"""
    aw_client = ActivityWatchClient()
    
    # Get data for the last 24 hours
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=1)
    
    print("🔍 DEBUGGING WINDOW TITLES FROM ACTIVITYWATCH")
    print("=" * 60)
    
    try:
        # Get raw activity data
        activity_data = aw_client.get_activity_data(start, end)
        
        print(f"📊 Total activities found: {len(activity_data)}")
        print("\n🏆 TOP 20 WINDOW TITLES BY DURATION:")
        print("-" * 60)
        
        # Group by window title and sum durations
        title_stats = {}
        for activity in activity_data:
            title = activity['window_title']
            app_name = activity['application_name']
            duration = activity['duration']
            
            # Skip very short activities
            if duration < 10:
                continue
            
            key = f"{title}|{app_name}"
            if key not in title_stats:
                title_stats[key] = {
                    'window_title': title,
                    'application_name': app_name,
                    'total_duration': 0,
                    'activity_count': 0
                }
            
            title_stats[key]['total_duration'] += duration
            title_stats[key]['activity_count'] += 1
        
        # Sort by duration and show top 20
        sorted_titles = sorted(
            title_stats.values(), 
            key=lambda x: x['total_duration'], 
            reverse=True
        )[:20]
        
        for i, title in enumerate(sorted_titles, 1):
            duration_hours = title['total_duration'] / 3600
            print(f"{i:2d}. {title['window_title'][:80]:<80} | {title['application_name']:<20} | {duration_hours:.2f}h")
        
        print(f"\n🔍 SPECIFIC SEARCHES:")
        print("-" * 60)
        
        # Look for specific terms you mentioned
        search_terms = ['waree', 'ajax-contact', 'salesform', 'validation', 'claude', 'chatgpt', 'kiki', 'terminus', 'istana', 'leads']
        
        for term in search_terms:
            matching_titles = [
                activity for activity in activity_data 
                if term.lower() in activity['window_title'].lower() and activity['duration'] > 5
            ]
            
            if matching_titles:
                print(f"\n🎯 Found '{term}' in {len(matching_titles)} activities:")
                for activity in matching_titles[:5]:  # Show top 5
                    duration_min = activity['duration'] / 60
                    print(f"   • {activity['window_title'][:100]} ({duration_min:.1f}m)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    debug_window_titles()
