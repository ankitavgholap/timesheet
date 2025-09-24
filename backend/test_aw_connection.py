#!/usr/bin/env python3
"""
Test ActivityWatch Connection and Fix Issues
"""

import requests
import json
from datetime import datetime, timezone, timedelta

def test_activitywatch_connection():
    """Test different ways to connect to ActivityWatch"""
    
    # Different URLs to try
    test_urls = [
        "http://127.0.0.1:5600",
        "http://localhost:5600", 
        "http://0.0.0.0:5600"
    ]
    
    print("🔍 Testing ActivityWatch connections...")
    
    for url in test_urls:
        try:
            print(f"\n📡 Testing: {url}")
            
            # Test info endpoint
            info_response = requests.get(f"{url}/api/0/info", timeout=5)
            
            if info_response.status_code == 200:
                info_data = info_response.json()
                print(f"   ✅ Connection successful!")
                print(f"   📊 ActivityWatch version: {info_data.get('version', 'unknown')}")
                
                # Test buckets endpoint
                buckets_response = requests.get(f"{url}/api/0/buckets", timeout=5)
                if buckets_response.status_code == 200:
                    buckets = buckets_response.json()
                    print(f"   📦 Found {len(buckets)} buckets:")
                    for bucket_name in list(buckets.keys())[:5]:  # Show first 5
                        print(f"      - {bucket_name}")
                    
                    # Test getting recent data
                    end_time = datetime.now(timezone.utc)
                    start_time = end_time - timedelta(hours=1)
                    
                    for bucket_name in list(buckets.keys())[:2]:  # Test first 2 buckets
                        if 'afk' not in bucket_name.lower():  # Skip AFK buckets
                            events_url = f"{url}/api/0/buckets/{bucket_name}/events"
                            params = {
                                'start': start_time.isoformat(),
                                'end': end_time.isoformat(),
                                'limit': 5
                            }
                            
                            try:
                                events_response = requests.get(events_url, params=params, timeout=5)
                                if events_response.status_code == 200:
                                    events = events_response.json()
                                    print(f"   📈 {bucket_name}: {len(events)} recent events")
                            except:
                                print(f"   ⚠️  {bucket_name}: Could not fetch events")
                    
                    return url  # Return working URL
                else:
                    print(f"   ❌ Could not access buckets")
            else:
                print(f"   ❌ HTTP {info_response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection refused")
        except requests.exceptions.Timeout:
            print(f"   ❌ Connection timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

def create_fixed_data_puller(working_url):
    """Create a fixed data puller script with the working URL"""
    
    fixed_script = f'''#!/usr/bin/env python3
"""
Fixed ActivityWatch Data Puller - Working Version
Auto-generated with working URL: {working_url}
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL")

# FIXED: Use the working ActivityWatch URL
ACTIVITYWATCH_URL = "{working_url}"

def pull_activity_data():
    """Pull data from ActivityWatch and save to database"""
    print("🔄 Pulling ActivityWatch data...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Get buckets
        buckets_response = requests.get(f"{{ACTIVITYWATCH_URL}}/api/0/buckets", timeout=10)
        if buckets_response.status_code != 200:
            print("❌ Could not fetch buckets")
            return
        
        buckets = buckets_response.json()
        print(f"📦 Found {{len(buckets)}} buckets")
        
        # Get recent data (last 1 hour)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        activities = []
        
        for bucket_name, bucket_info in buckets.items():
            # Skip AFK buckets
            if 'afk' in bucket_name.lower():
                continue
            
            try:
                events_url = f"{{ACTIVITYWATCH_URL}}/api/0/buckets/{{bucket_name}}/events"
                params = {{
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'limit': 100
                }}
                
                events_response = requests.get(events_url, params=params, timeout=10)
                if events_response.status_code != 200:
                    continue
                
                events = events_response.json()
                print(f"📈 {{bucket_name}}: {{len(events)}} events")
                
                for event in events:
                    data = event.get('data', {{}})
                    duration = event.get('duration', 0)
                    
                    if duration < 5:  # Skip very short activities
                        continue
                    
                    activity = {{
                        'developer_id': 'ankita_gholap',  # Your developer ID
                        'developer_name': 'Ankita Gholap',
                        'application_name': data.get('app', data.get('application', 'Unknown')),
                        'window_title': data.get('title', ''),
                        'duration': duration,
                        'timestamp': datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00')),
                        'bucket_name': bucket_name,
                        'category': 'general'
                    }}
                    
                    activities.append(activity)
                    
            except Exception as e:
                print(f"⚠️  Error processing {{bucket_name}}: {{e}}")
                continue
        
        # Save to database
        if activities:
            with engine.connect() as conn:
                insert_query = text("""
                    INSERT INTO activity_records (
                        developer_id, developer_name, application_name, 
                        window_title, duration, timestamp, bucket_name, 
                        category, created_at
                    ) VALUES (
                        :developer_id, :developer_name, :application_name,
                        :window_title, :duration, :timestamp, :bucket_name,
                        :category, NOW()
                    )
                """)
                
                saved_count = 0
                for activity in activities:
                    try:
                        conn.execute(insert_query, activity)
                        saved_count += 1
                    except:
                        continue  # Skip duplicates
                
                conn.commit()
                print(f"💾 Saved {{saved_count}} activities to database")
        else:
            print("📝 No new activities to save")
                
    except Exception as e:
        print(f"❌ Error: {{e}}")

if __name__ == "__main__":
    pull_activity_data()
'''
    
    # Save the fixed script
    with open('fixed_data_puller.py', 'w', encoding='utf-8') as f:
        f.write(fixed_script)
    
    print(f"\n✅ Created fixed_data_puller.py with working URL: {working_url}")
    print("\n📋 To use:")
    print("   python fixed_data_puller.py")

def main():
    print("🔧 ActivityWatch Connection Tester & Fixer")
    print("=" * 50)
    
    # Test connections
    working_url = test_activitywatch_connection()
    
    if working_url:
        print(f"\n🎉 Found working ActivityWatch URL: {working_url}")
        
        # Create fixed data puller
        create_fixed_data_puller(working_url)
        
        print(f"\n🚀 Next steps:")
        print("1. Run the fixed puller: python fixed_data_puller.py")
        print("2. Check your database for new activity data")
        print("3. Your dashboard should now show data!")
        
    else:
        print("\n❌ Could not connect to ActivityWatch on any URL")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure ActivityWatch is running")
        print("2. Check Windows Firewall settings")
        print("3. Try restarting ActivityWatch")
        print("4. Check if another application is using port 5600")

if __name__ == "__main__":
    main()
