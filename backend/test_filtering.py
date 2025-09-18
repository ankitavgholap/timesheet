#!/usr/bin/env python3
"""
Test the new filtering logic
"""
from activitywatch_client import ActivityWatchClient
from datetime import datetime, timezone

def test_filtering():
    """Test the filtering logic with current date range"""
    aw_client = ActivityWatchClient()
    
    # Use current date range (no hardcoding)
    end = datetime.now(timezone.utc)
    start = datetime(end.year, end.month, 1, tzinfo=timezone.utc)  # Start of current month
    
    print(f"🔍 TESTING FILTERING LOGIC")
    print(f"📅 Date range: {start.date()} to {end.date()}")
    print("=" * 60)
    
    try:
        # Get top window titles with filtering
        top_titles = aw_client.get_top_window_titles(start, end, limit=30)
        
        print(f"📊 Found {len(top_titles)} work-related window titles")
        print("\n🏆 TOP WORK-RELATED ACTIVITIES:")
        print("-" * 80)
        
        for i, title in enumerate(top_titles, 1):
            duration_hours = title['total_duration'] / 3600
            project_name = title.get('project_info', {}).get('project_name', 'Unknown')
            project_type = title.get('project_info', {}).get('project_type', 'Work')
            
            print(f"{i:2d}. {title['window_title'][:60]:<60} | {project_type:<15} | {duration_hours:5.2f}h")
        
        # Show what was filtered out by testing some sample activities
        print(f"\n🚫 TESTING FILTER LOGIC:")
        print("-" * 40)
        
        test_activities = [
            ("YouTube Music - Google Chrome", "chrome.exe"),
            ("jQuery AJAX Salesforce Form Validation - Claude", "chrome.exe"),
            ("Windows Default Lock Screen", "LockApp.exe"),
            ("ajax-contact.js - Visual Studio Code", "Code.exe"),
            ("Dashboard - WAAREE Admin - Google Chrome", "chrome.exe"),
            ("Aaj Ka Khiladi (Ninnu Kori) Latest Hindi Dubbed Movie", "chrome.exe"),
            ("Claude - Google Chrome", "chrome.exe"),
            ("Instagram - Google Chrome", "chrome.exe"),
            ("localhost:3000 - React App", "chrome.exe"),
            ("GitHub - Project Repository", "chrome.exe")
        ]
        
        for title, app in test_activities:
            is_filtered = aw_client._is_non_work_activity(title, app)
            status = "❌ FILTERED" if is_filtered else "✅ KEPT"
            print(f"{status} | {title}")
        
        return top_titles
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_filtering()
