#!/usr/bin/env python3
"""
Simple Windows ActivityWatch to Database Sync
No complex setup needed - just run this!
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import time

# Load your database connection
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL")

def sync_activitywatch_to_database():
    """Pull data from your local ActivityWatch and save to database"""
    print("🔄 Syncing ActivityWatch data to database...")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        
        # Connect to your local ActivityWatch
        aw_url = "http://127.0.0.1:5600"  # Your ActivityWatch URL
        
        print(f"📡 Connecting to ActivityWatch at {aw_url}")
        
        # Get buckets
        buckets_response = requests.get(f"{aw_url}/api/0/buckets", timeout=10)
        if buckets_response.status_code != 200:
            print("❌ Could not connect to ActivityWatch - make sure it's running!")
            return False
        
        buckets = buckets_response.json()
        print(f"📦 Found {len(buckets)} buckets")
        
        # Get data from last 2 hours
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=2)
        
        activities_to_save = []
        
        for bucket_name, bucket_info in buckets.items():
            # Skip AFK buckets
            if 'afk' in bucket_name.lower():
                continue
            
            print(f"📈 Processing {bucket_name}...")
            
            try:
                # Get events from this bucket
                events_url = f"{aw_url}/api/0/buckets/{bucket_name}/events"
                params = {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'limit': 200
                }
                
                events_response = requests.get(events_url, params=params, timeout=10)
                if events_response.status_code != 200:
                    print(f"⚠️  Could not get events from {bucket_name}")
                    continue
                
                events = events_response.json()
                print(f"   Found {len(events)} events")
                
                for event in events:
                    data = event.get('data', {})
                    duration = event.get('duration', 0)
                    timestamp = event.get('timestamp', '')
                    
                    # Skip very short activities
                    if duration < 10:
                        continue
                    
                    activity = {
                        'developer_id': 'ankita_gholap',
                        'developer_name': 'Ankita Gholap',
                        'application_name': data.get('app', data.get('application', 'Unknown')),
                        'window_title': data.get('title', ''),
                        'url': data.get('url', ''),
                        'duration': duration,
                        'timestamp': datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                        'bucket_name': bucket_name,
                        'category': categorize_activity(data.get('app', '')),
                        'created_at': datetime.now(timezone.utc)
                    }
                    
                    activities_to_save.append(activity)
                    
            except Exception as e:
                print(f"⚠️  Error processing {bucket_name}: {e}")
                continue
        
        # Save to database
        if activities_to_save:
            print(f"💾 Saving {len(activities_to_save)} activities to database...")
            
            with engine.connect() as conn:
                # Insert query
                insert_query = text("""
                    INSERT INTO activity_records (
                        developer_id, developer_name, application_name,
                        window_title, url, duration, timestamp, bucket_name,
                        category, created_at
                    ) VALUES (
                        :developer_id, :developer_name, :application_name,
                        :window_title, :url, :duration, :timestamp, :bucket_name,
                        :category, :created_at
                    )
                    ON CONFLICT DO NOTHING
                """)
                
                saved_count = 0
                for activity in activities_to_save:
                    try:
                        conn.execute(insert_query, activity)
                        saved_count += 1
                    except Exception as e:
                        # Skip duplicates or errors
                        continue
                
                conn.commit()
                print(f"✅ Successfully saved {saved_count} activities!")
                return True
        else:
            print("📝 No new activities to save")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def categorize_activity(app_name):
    """Simple categorization of activities"""
    if not app_name:
        return 'unknown'
    
    app_lower = app_name.lower()
    
    if 'cursor' in app_lower or 'vscode' in app_lower or 'code' in app_lower:
        return 'development'
    elif 'chrome' in app_lower or 'firefox' in app_lower or 'edge' in app_lower:
        return 'browser'
    elif 'terminal' in app_lower or 'cmd' in app_lower or 'powershell' in app_lower:
        return 'terminal'
    else:
        return 'general'

def continuous_sync():
    """Run continuous sync every 5 minutes"""
    print("🚀 Starting continuous ActivityWatch sync...")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        while True:
            print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Starting sync...")
            
            if sync_activitywatch_to_database():
                print("✅ Sync completed successfully")
            else:
                print("❌ Sync failed")
            
            print("⏳ Waiting 5 minutes for next sync...")
            time.sleep(300)  # Wait 5 minutes
            
    except KeyboardInterrupt:
        print("\n🛑 Sync stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    import sys
    
    print("🔄 ActivityWatch Database Sync")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        continuous_sync()
    else:
        # Single sync
        print("Running one-time sync...")
        if sync_activitywatch_to_database():
            print("\n🎉 Sync completed! Check your dashboard for data.")
        else:
            print("\n❌ Sync failed. Make sure ActivityWatch is running.")
        
        print("\nTo run continuous sync: python simple_sync.py --continuous")

if __name__ == "__main__":
    main()
