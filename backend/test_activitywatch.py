#!/usr/bin/env python3
"""
Test script to check ActivityWatch connection and data extraction
"""
from datetime import datetime, timedelta
from activitywatch_client import ActivityWatchClient
import json

def test_activitywatch():
    """Test ActivityWatch connection and data extraction"""
    print("🔍 Testing ActivityWatch Connection...")
    print("=" * 50)
    
    client = ActivityWatchClient()
    
    # Test connection
    if not client.test_connection():
        print("❌ Cannot connect to ActivityWatch!")
        print("Make sure ActivityWatch is running on http://localhost:5600")
        return
    
    print("✅ Connected to ActivityWatch successfully!")
    
    # Get buckets
    print("\n📦 Available Buckets:")
    buckets = client.get_buckets()
    for bucket_name, bucket_info in buckets.items():
        print(f"  - {bucket_name}: {bucket_info.get('type', 'unknown')}")
    
    # Get recent activity data
    print("\n📊 Recent Activity Data (last 24 hours):")
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    print(f"Querying from {start_time} to {end_time}")
    
    # First, let's test getting raw events from each bucket
    print("\n🔍 Raw Events from Buckets:")
    for bucket_name, bucket_info in buckets.items():
        if 'afk' in bucket_name.lower():
            continue  # Skip AFK bucket
            
        print(f"\n📦 Bucket: {bucket_name}")
        events = client.get_events(bucket_name, start_time, end_time)
        print(f"  Found {len(events)} raw events")
        
        # Show first few events
        for i, event in enumerate(events[:3]):
            data = event.get('data', {})
            duration = event.get('duration', 0)
            timestamp = event.get('timestamp', '')
            
            app_name = data.get('app', data.get('application', 'Unknown'))
            window_title = data.get('title', '')
            
            print(f"  {i+1}. {app_name} | {duration:.1f}s | {window_title[:60]}")
    
    # Now get processed activity data
    activity_data = client.get_activity_data(start_time, end_time)
    
    print(f"Found {len(activity_data)} activities")
    
    # Show top 10 activities
    print("\n🔝 Top 10 Recent Activities:")
    print("-" * 80)
    for i, activity in enumerate(activity_data[:10]):
        duration_min = activity['duration'] / 60
        print(f"{i+1:2d}. {activity['application_name']:<20} | {duration_min:5.1f}m | {activity['window_title'][:50]}")
        if activity.get('detailed_activity'):
            print(f"    📋 Detailed: {activity['detailed_activity']}")
        if activity.get('url'):
            print(f"    🌐 URL: {activity['url']}")
        if activity.get('file_path'):
            print(f"    📁 File: {activity['file_path']}")
        print()
    
    # Test specific window titles you mentioned
    print("\n🎯 Looking for specific window titles...")
    target_titles = [
        "Claude - Google Chrome",
        "timesheet - Cursor",
        ".env - timesheet - Cursor",
        "package.json - timesheet - Cursor"
    ]
    
    found_titles = []
    for activity in activity_data:
        for target in target_titles:
            if target.lower() in activity['window_title'].lower():
                found_titles.append(activity)
                break
    
    if found_titles:
        print(f"✅ Found {len(found_titles)} matching activities:")
        for activity in found_titles:
            print(f"  - {activity['window_title']} ({activity['duration']/60:.1f}m)")
            print(f"    App: {activity['application_name']}")
            print(f"    Category: {activity['category']}")
            if activity.get('detailed_activity'):
                print(f"    Detailed: {activity['detailed_activity']}")
    else:
        print("❌ No matching window titles found in recent data")
        print("Try running this script when you have those applications open")

if __name__ == "__main__":
    test_activitywatch()
