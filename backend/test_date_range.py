#!/usr/bin/env python3
"""
Test the specific date range September 1-15 to match the screenshot
"""
from activitywatch_client import ActivityWatchClient
from datetime import datetime, timezone

def test_september_range():
    """Test September 1-15 date range"""
    aw_client = ActivityWatchClient()
    
    # Set the exact date range from the screenshot: September 1-15, 2024
    start = datetime(2024, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2024, 9, 15, 23, 59, 59, tzinfo=timezone.utc)
    
    print(f"🔍 TESTING SEPTEMBER 1-15 DATE RANGE")
    print(f"📅 Start: {start}")
    print(f"📅 End: {end}")
    print("=" * 60)
    
    try:
        # Get top window titles for this exact range
        top_titles = aw_client.get_top_window_titles(start, end, limit=50)
        
        print(f"📊 Found {len(top_titles)} window titles")
        print("\n🏆 TOP WINDOW TITLES (Sep 1-15):")
        print("-" * 80)
        
        for i, title in enumerate(top_titles[:30], 1):
            duration_hours = title['total_duration'] / 3600
            project_name = title.get('project_info', {}).get('project_name', 'Unknown')
            print(f"{i:2d}. {title['window_title'][:60]:<60} | {title['application_name']:<15} | {duration_hours:5.2f}h | {project_name[:20]}")
        
        # Search for the specific terms you mentioned
        search_terms = ['waree', 'ajax', 'salesform', 'validation', 'claude', 'chatgpt', 'kiki', 'terminus', 'istana', 'leads']
        
        print(f"\n🔍 SEARCHING FOR YOUR MENTIONED TERMS:")
        print("-" * 60)
        
        for term in search_terms:
            matches = [
                title for title in top_titles 
                if term.lower() in title['window_title'].lower()
            ]
            
            if matches:
                print(f"\n✅ Found '{term}' in {len(matches)} window titles:")
                for match in matches[:3]:
                    duration_hours = match['total_duration'] / 3600
                    print(f"   • {match['window_title'][:70]} ({duration_hours:.2f}h)")
            else:
                print(f"❌ '{term}' not found in current results")
        
        return top_titles
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_september_range()
