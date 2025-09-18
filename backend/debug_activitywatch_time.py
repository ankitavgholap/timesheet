#!/usr/bin/env python3
"""
Debug ActivityWatch time calculation to understand why durations are so small
"""
from activitywatch_client import ActivityWatchClient
from datetime import datetime, timezone, timedelta

def debug_activitywatch_time():
    """Debug ActivityWatch time calculation"""
    aw_client = ActivityWatchClient()
    
    # Test with today's data
    end = datetime.now(timezone.utc)
    start = end.replace(hour=0, minute=0, second=0, microsecond=0)  # Start of today
    
    print("🔍 DEBUGGING ACTIVITYWATCH TIME CALCULATION")
    print(f"📅 Date range: {start} to {end}")
    print("=" * 80)
    
    try:
        # Get raw ActivityWatch data
        activity_data = aw_client.get_activity_data(start, end)
        
        print(f"📊 Total events fetched: {len(activity_data)}")
        
        if not activity_data:
            print("❌ No activity data found!")
            return
        
        # Analyze the data
        total_duration = 0
        duration_breakdown = {}
        app_durations = {}
        
        print("\n📋 SAMPLE EVENTS (first 10):")
        print("-" * 80)
        
        for i, activity in enumerate(activity_data[:10]):
            duration_sec = activity['duration']
            duration_min = duration_sec / 60
            total_duration += duration_sec
            
            app = activity.get('application_name', 'Unknown')
            category = activity.get('category', 'Unknown')
            
            print(f"{i+1:2d}. {activity['timestamp'].strftime('%H:%M:%S')} | "
                  f"{app[:20]:20s} | {duration_sec:6.1f}s ({duration_min:5.1f}m) | {category}")
            
            # Track by category
            if category not in duration_breakdown:
                duration_breakdown[category] = 0
            duration_breakdown[category] += duration_sec
            
            # Track by app
            if app not in app_durations:
                app_durations[app] = 0
            app_durations[app] += duration_sec
        
        print(f"\n📈 TOTAL DURATION ANALYSIS:")
        print(f"   Raw total: {total_duration:.1f} seconds = {total_duration/60:.1f} minutes = {total_duration/3600:.2f} hours")
        
        print(f"\n📊 DURATION BY CATEGORY:")
        print("-" * 50)
        for category, duration in sorted(duration_breakdown.items(), key=lambda x: x[1], reverse=True):
            hours = duration / 3600
            minutes = duration / 60
            print(f"   {category:20s}: {hours:6.2f}h ({minutes:7.1f}m)")
        
        print(f"\n🎯 TOP APPLICATIONS BY TIME:")
        print("-" * 50)
        sorted_apps = sorted(app_durations.items(), key=lambda x: x[1], reverse=True)[:10]
        for app, duration in sorted_apps:
            hours = duration / 3600
            minutes = duration / 60
            print(f"   {app[:30]:30s}: {hours:6.2f}h ({minutes:7.1f}m)")
        
        # Check for gaps or issues
        print(f"\n🔍 DATA QUALITY CHECK:")
        print("-" * 50)
        
        # Check time range
        timestamps = [activity['timestamp'] for activity in activity_data]
        earliest = min(timestamps)
        latest = max(timestamps)
        time_span = (latest - earliest).total_seconds() / 3600
        
        print(f"   First event: {earliest.strftime('%H:%M:%S')}")
        print(f"   Last event:  {latest.strftime('%H:%M:%S')}")
        print(f"   Time span:   {time_span:.2f} hours")
        print(f"   Coverage:    {(total_duration/3600)/time_span*100:.1f}% of time span" if time_span > 0 else "   Coverage: N/A")
        
        # Check for very short events
        short_events = [a for a in activity_data if a['duration'] < 5]  # Less than 5 seconds
        print(f"   Short events (<5s): {len(short_events)}/{len(activity_data)} ({len(short_events)/len(activity_data)*100:.1f}%)")
        
        # Check for long events
        long_events = [a for a in activity_data if a['duration'] > 300]  # More than 5 minutes
        print(f"   Long events (>5m): {len(long_events)}/{len(activity_data)} ({len(long_events)/len(activity_data)*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_activitywatch_time()







