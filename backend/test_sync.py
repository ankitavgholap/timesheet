# Create this as: backend/test_sync.py

from activitywatch_sync import ActivityWatchSync
from datetime import datetime, timezone
import requests

def test_activitywatch_connection():
    """Test if ActivityWatch is accessible"""
    try:
        response = requests.get("http://localhost:5600/api/0/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print("✅ ActivityWatch is running!")
            print(f"   Version: {info.get('version', 'Unknown')}")
            print(f"   Hostname: {info.get('hostname', 'Unknown')}")
            return True
        else:
            print(f"❌ ActivityWatch responded with error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to ActivityWatch: {e}")
        print("   Make sure ActivityWatch is running on http://localhost:5600")
        return False

def test_sync():
    """Test the sync process"""
    print("🔄 Testing ActivityWatch sync...\n")
    
    # Test connection first
    if not test_activitywatch_connection():
        return
    
    # Test sync
    sync = ActivityWatchSync()
    
    # Sync today's data
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"\n🔄 Syncing data for {sync.developer_name}...")
    success = sync.sync_activitywatch_data(today)
    
    if success:
        print("✅ Sync completed successfully!")
        
        # Get summary
        summary = sync.get_summary(today)
        print(f"\n📊 Summary for today:")
        print(f"   Total time: {summary['total_time']:.2f} hours")
        print(f"   Active projects: {summary['active_projects']}")
        print(f"   Categories found: {len(summary['data'])}")
        
        for activity in summary['data']:
            print(f"   - {activity['category']}: {activity['duration']:.2f}h ({activity['count']} activities)")
        
        print(f"\n🎉 Success! Your ActivityWatch data is now available in the dashboard.")
        print(f"Visit: http://localhost:8000/developers-list")
        
    else:
        print("❌ Sync failed!")

if __name__ == "__main__":
    test_sync()