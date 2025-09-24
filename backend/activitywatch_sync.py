# ActivityWatch Data Sync Service
import requests
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from database import DATABASE_URL
from config import Config
import json
import time

class ActivityWatchSync:
    def __init__(self):
        self.aw_host = Config.ACTIVITYWATCH_HOST
        self.developer_name = Config.LOCAL_DEVELOPER_NAME
        self.engine = create_engine(DATABASE_URL)
    
    def get_activitywatch_buckets(self):
        """Get available ActivityWatch buckets"""
        try:
            response = requests.get(f"{self.aw_host}/api/0/buckets", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting buckets: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error connecting to ActivityWatch: {e}")
            return {}
    
    def get_window_events(self, bucket_name, start_time, end_time):
        """Get window events from ActivityWatch"""
        try:
            response = requests.get(
                f"{self.aw_host}/api/0/buckets/{bucket_name}/events",
                params={
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'limit': 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting events from {bucket_name}: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting events from {bucket_name}: {e}")
            return []
    
    def categorize_application(self, app_name, window_title=""):
        """Categorize application based on name and window title"""
        app_lower = app_name.lower()
        title_lower = window_title.lower()
        
        # Development tools
        if any(dev_app in app_lower for dev_app in [
            'vscode', 'code', 'cursor', 'pycharm', 'intellij', 'sublime', 
            'atom', 'vim', 'emacs', 'notepad++'
        ]):
            return 'IDE'
        
        # Browsers
        if any(browser in app_lower for browser in [
            'chrome', 'firefox', 'safari', 'edge', 'brave', 'opera'
        ]):
            return 'Browser'
        
        # Database tools
        if any(db_tool in app_lower for db_tool in [
            'datagrip', 'pgadmin', 'phpmyadmin', 'mysql', 'postgresql', 'mongodb'
        ]):
            return 'Database'
        
        # Communication tools
        if any(comm_tool in app_lower for comm_tool in [
            'slack', 'teams', 'discord', 'telegram', 'whatsapp', 'zoom', 'skype'
        ]):
            return 'Communication'
        
        # Productivity tools
        if any(prod_tool in app_lower for prod_tool in [
            'notion', 'obsidian', 'trello', 'asana', 'jira', 'confluence', 
            'excel', 'word', 'powerpoint', 'outlook'
        ]):
            return 'Productivity'
        
        # File management
        if any(file_tool in app_lower for file_tool in [
            'filezilla', 'winscp', 'explorer', 'finder', 'terminal', 'cmd', 'powershell'
        ]):
            return 'System'
        
        # Entertainment
        if any(ent_app in app_lower for ent_app in [
            'spotify', 'youtube', 'netflix', 'twitch', 'steam', 'discord'
        ]) or any(ent_word in title_lower for ent_word in ['music', 'video', 'game']):
            return 'Entertainment'
        
        # Default
        return 'Other'
    
    def sync_activitywatch_data(self, start_date=None, end_date=None):
        """Sync data from ActivityWatch to database"""
        print(f"🔄 Syncing ActivityWatch data for {self.developer_name}...")
        
        # Default to today if no dates provided
        if not start_date:
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        # Get available buckets
        buckets = self.get_activitywatch_buckets()
        if not buckets:
            print("❌ No ActivityWatch buckets found!")
            return False
        
        print(f"📊 Found {len(buckets)} ActivityWatch buckets")
        
        # Find window watcher bucket (usually contains window/app data)
        window_bucket = None
        for bucket_name in buckets.keys():
            if 'window' in bucket_name.lower():
                window_bucket = bucket_name
                break
        
        if not window_bucket:
            print("❌ No window watcher bucket found!")
            return False
        
        print(f"📋 Using bucket: {window_bucket}")
        
        # Get events from ActivityWatch
        events = self.get_window_events(window_bucket, start_date, end_date)
        if not events:
            print("❌ No events found in ActivityWatch!")
            return False
        
        print(f"📥 Retrieved {len(events)} events from ActivityWatch")
        
        # Clear existing data for this developer and date range
        with self.engine.connect() as conn:
            conn.execute(text("""
                DELETE FROM activity_records 
                WHERE developer_id = :dev_id 
                AND timestamp >= :start_date 
                AND timestamp <= :end_date
            """), {
                "dev_id": self.developer_name,
                "start_date": start_date,
                "end_date": end_date
            })
            conn.commit()
        
        # Process and store events
        stored_count = 0
        with self.engine.connect() as conn:
            for event in events:
                try:
                    # Extract event data
                    data = event.get('data', {})
                    app_name = data.get('app', 'Unknown')
                    window_title = data.get('title', '')
                    duration = event.get('duration', 0)
                    timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    
                    # Skip very short events (less than 10 seconds)
                    if duration < 10:
                        continue
                    
                    # Categorize the application
                    category = self.categorize_application(app_name, window_title)
                    
                    # Store in database
                    conn.execute(text("""
                        INSERT INTO activity_records 
                        (developer_id, application_name, window_title, category, duration, timestamp)
                        VALUES (:dev_id, :app, :title, :category, :duration, :timestamp)
                    """), {
                        "dev_id": self.developer_name,
                        "app": app_name,
                        "title": window_title,
                        "category": category,
                        "duration": duration,
                        "timestamp": timestamp
                    })
                    stored_count += 1
                    
                except Exception as e:
                    print(f"Error processing event: {e}")
                    continue
            
            conn.commit()
        
        print(f"✅ Stored {stored_count} activity records for {self.developer_name}")
        return True
    
    def get_summary(self, start_date=None, end_date=None):
        """Get activity summary from database"""
        if not start_date:
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        with self.engine.connect() as conn:
            # Get activity summary
            result = conn.execute(text("""
                SELECT 
                    category,
                    SUM(duration) as total_duration,
                    COUNT(*) as activity_count
                FROM activity_records 
                WHERE developer_id = :dev_id 
                AND timestamp >= :start_date 
                AND timestamp <= :end_date
                GROUP BY category
                ORDER BY total_duration DESC
            """), {
                "dev_id": self.developer_name,
                "start_date": start_date,
                "end_date": end_date
            }).fetchall()
            
            activities = []
            colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0']
            
            for i, row in enumerate(result):
                activities.append({
                    "category": row[0],
                    "duration": row[1] / 3600.0,  # Convert to hours
                    "count": row[2],
                    "color": colors[i % len(colors)]
                })
            
            # Get total time and project count
            total_result = conn.execute(text("""
                SELECT 
                    SUM(duration) as total_duration,
                    COUNT(DISTINCT application_name) as project_count
                FROM activity_records 
                WHERE developer_id = :dev_id 
                AND timestamp >= :start_date 
                AND timestamp <= :end_date
            """), {
                "dev_id": self.developer_name,
                "start_date": start_date,
                "end_date": end_date
            }).fetchone()
            
            total_time = (total_result[0] or 0) / 3600.0  # Convert to hours
            project_count = total_result[1] or 0
            
            return {
                "data": activities,
                "total_time": total_time,
                "active_projects": project_count,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }

def manual_sync():
    """Manual sync function for testing"""
    sync = ActivityWatchSync()
    
    # Sync today's data
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    success = sync.sync_activitywatch_data(today, tomorrow)
    
    if success:
        summary = sync.get_summary(today, tomorrow)
        print(f"\n📊 Summary for {sync.developer_name}:")
        print(f"   Total time: {summary['total_time']:.2f} hours")
        print(f"   Active projects: {summary['active_projects']}")
        print(f"   Categories: {len(summary['data'])}")
        
        for activity in summary['data']:
            print(f"   - {activity['category']}: {activity['duration']:.2f}h")

if __name__ == "__main__":
    manual_sync()
