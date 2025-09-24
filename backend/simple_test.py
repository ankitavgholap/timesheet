# Simple test without imports
import requests
import os

def test_simple():
    print("🔄 Testing ActivityWatch connection...\n")
    
    # Test ActivityWatch connection
    try:
        response = requests.get("http://localhost:5600/api/0/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print("✅ ActivityWatch is running!")
            print(f"   Version: {info.get('version', 'Unknown')}")
            print(f"   Hostname: {info.get('hostname', 'Unknown')}")
            print(f"   Device ID: {info.get('device_id', 'Unknown')}")
            
            # Test getting buckets
            buckets_response = requests.get("http://localhost:5600/api/0/buckets", timeout=10)
            if buckets_response.status_code == 200:
                buckets = buckets_response.json()
                print(f"\n📊 Available buckets:")
                for bucket_name, bucket_info in buckets.items():
                    print(f"   - {bucket_name}: {bucket_info.get('type', 'Unknown')}")
                
                # Look for window bucket
                window_bucket = None
                for bucket_name in buckets.keys():
                    if 'window' in bucket_name.lower():
                        window_bucket = bucket_name
                        break
                
                if window_bucket:
                    print(f"\n✅ Found window bucket: {window_bucket}")
                    
                    # Test getting some events
                    from datetime import datetime, timezone, timedelta
                    end_time = datetime.now(timezone.utc)
                    start_time = end_time - timedelta(hours=2)  # Last 2 hours
                    
                    events_response = requests.get(
                        f"http://localhost:5600/api/0/buckets/{window_bucket}/events",
                        params={
                            'start': start_time.isoformat(),
                            'end': end_time.isoformat(),
                            'limit': 10
                        },
                        timeout=15
                    )
                    
                    if events_response.status_code == 200:
                        events = events_response.json()
                        print(f"\n📥 Found {len(events)} recent events:")
                        for i, event in enumerate(events[:5]):
                            data = event.get('data', {})
                            app = data.get('app', 'Unknown')
                            title = data.get('title', 'No title')[:50]
                            duration = event.get('duration', 0)
                            print(f"   {i+1}. {app} | {title}... | {duration:.1f}s")
                        
                        if len(events) > 0:
                            print(f"\n🎉 ActivityWatch is working perfectly!")
                            print(f"✅ You can now start your backend and it will sync this data automatically.")
                        else:
                            print(f"\n⚠️  No recent events found. Make sure you've been using your computer.")
                    else:
                        print(f"❌ Could not get events: {events_response.status_code}")
                else:
                    print(f"\n❌ No window bucket found. Available buckets:")
                    for name in buckets.keys():
                        print(f"   - {name}")
            else:
                print(f"❌ Could not get buckets: {buckets_response.status_code}")
        else:
            print(f"❌ ActivityWatch responded with error: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to ActivityWatch: {e}")
        print("\n💡 To fix this:")
        print("   1. Make sure ActivityWatch is installed and running")
        print("   2. Check if http://localhost:5600 opens in your browser")
        print("   3. If ActivityWatch is on a different port, update the URL")

if __name__ == "__main__":
    test_simple()
