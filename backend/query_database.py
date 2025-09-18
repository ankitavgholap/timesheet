#!/usr/bin/env python3
"""
Simple Database Query Tool - Easy way to check your data
"""
from database import SessionLocal
import models
from sqlalchemy import text, func
from datetime import datetime, timezone, timedelta

def query_database():
    """Simple queries to check your data"""
    db = SessionLocal()
    
    try:
        print("🔍 SIMPLE DATABASE QUERIES")
        print("=" * 50)
        
        # 1. Total Statistics
        print("📊 QUICK STATS:")
        print("-" * 20)
        
        total_users = db.query(models.User).count()
        total_activities = db.query(models.ActivityRecord).count()
        
        print(f"Users: {total_users}")
        print(f"Total Activities: {total_activities}")
        
        if total_activities > 0:
            # Total time tracked
            total_duration = db.query(func.sum(models.ActivityRecord.duration)).scalar() or 0
            total_hours = total_duration / 3600
            print(f"Total Hours Tracked: {total_hours:.2f}h")
            
            # Date range
            first_activity = db.query(models.ActivityRecord).order_by(models.ActivityRecord.timestamp.asc()).first()
            last_activity = db.query(models.ActivityRecord).order_by(models.ActivityRecord.timestamp.desc()).first()
            print(f"First Activity: {first_activity.timestamp.date()}")
            print(f"Last Activity: {last_activity.timestamp.date()}")
        
        print()
        
        # 2. Today's Activities
        print("📅 TODAY'S ACTIVITIES:")
        print("-" * 25)
        
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        today_activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp < tomorrow
        ).all()
        
        if today_activities:
            total_today = sum(a.duration for a in today_activities) / 3600
            print(f"Activities Today: {len(today_activities)}")
            print(f"Hours Today: {total_today:.2f}h")
            
            # Category breakdown
            categories = {}
            for activity in today_activities:
                cat = activity.category
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += activity.duration / 3600
            
            print("Categories Today:")
            for cat, hours in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {cat}: {hours:.2f}h")
        else:
            print("No activities today yet.")
        
        print()
        
        # 3. Last 7 Days Summary
        print("📈 LAST 7 DAYS:")
        print("-" * 20)
        
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        week_activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.timestamp >= week_ago
        ).all()
        
        if week_activities:
            total_week = sum(a.duration for a in week_activities) / 3600
            print(f"Activities This Week: {len(week_activities)}")
            print(f"Hours This Week: {total_week:.2f}h")
            print(f"Average Per Day: {total_week/7:.2f}h")
        
        print()
        
        # 4. Top Applications
        print("🏆 TOP APPLICATIONS (All Time):")
        print("-" * 35)
        
        app_stats = db.execute(text("""
            SELECT application_name, 
                   COUNT(*) as activity_count,
                   SUM(duration) as total_duration
            FROM activity_records 
            GROUP BY application_name 
            ORDER BY total_duration DESC 
            LIMIT 10
        """)).fetchall()
        
        for i, (app, count, duration) in enumerate(app_stats, 1):
            hours = duration / 3600 if duration else 0
            print(f"{i:2d}. {app}: {hours:.2f}h ({count} activities)")
        
        print()
        
        # 5. Recent Files Worked On
        print("📁 RECENT FILES (Development):")
        print("-" * 35)
        
        recent_files = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.category == 'development',
            models.ActivityRecord.file_path.isnot(None)
        ).order_by(models.ActivityRecord.timestamp.desc()).limit(10).all()
        
        if recent_files:
            for i, activity in enumerate(recent_files, 1):
                time_ago = datetime.now(timezone.utc) - activity.timestamp.replace(tzinfo=timezone.utc)
                if time_ago.days > 0:
                    time_str = f"{time_ago.days}d ago"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds//3600}h ago"
                else:
                    time_str = f"{time_ago.seconds//60}m ago"
                
                print(f"{i:2d}. {activity.file_path} ({time_str})")
        else:
            print("No development files tracked yet.")
        
        print()
        
        # 6. How to Access Database Directly
        print("🛠️ HOW TO ACCESS DATABASE DIRECTLY:")
        print("-" * 40)
        print("1. Using DataGrip (you already have this!):")
        print("   - Connect to: postgresql://postgres:asdf1234@localhost:5432/timesheet")
        print("   - Main table: activity_records")
        print("   - Users table: users")
        print()
        print("2. Using psql command line:")
        print("   psql -h localhost -U postgres -d timesheet")
        print("   \\dt  (list tables)")
        print("   SELECT * FROM activity_records LIMIT 10;")
        print()
        print("3. Using this Python script:")
        print("   python inspect_database.py")
        print("   python query_database.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def custom_query(query_type: str = "today"):
    """Run custom queries"""
    db = SessionLocal()
    
    try:
        if query_type == "today":
            print("📅 TODAY'S DETAILED BREAKDOWN:")
            print("-" * 35)
            
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Get today's activities by hour
            hourly_data = {}
            
            activities = db.query(models.ActivityRecord).filter(
                models.ActivityRecord.timestamp >= today,
                models.ActivityRecord.timestamp < tomorrow
            ).order_by(models.ActivityRecord.timestamp.asc()).all()
            
            for activity in activities:
                hour = activity.timestamp.hour
                if hour not in hourly_data:
                    hourly_data[hour] = {'duration': 0, 'activities': 0, 'categories': set()}
                
                hourly_data[hour]['duration'] += activity.duration
                hourly_data[hour]['activities'] += 1
                hourly_data[hour]['categories'].add(activity.category)
            
            for hour in sorted(hourly_data.keys()):
                data = hourly_data[hour]
                duration_min = data['duration'] / 60
                categories = ', '.join(data['categories'])
                print(f"{hour:2d}:00 - {duration_min:5.1f}min ({data['activities']} activities) - {categories}")
        
        elif query_type == "files":
            print("📁 FILES YOU'VE WORKED ON:")
            print("-" * 30)
            
            file_stats = db.execute(text("""
                SELECT file_path, 
                       COUNT(*) as sessions,
                       SUM(duration) as total_time,
                       MAX(timestamp) as last_worked
                FROM activity_records 
                WHERE file_path IS NOT NULL 
                  AND category = 'development'
                GROUP BY file_path 
                ORDER BY total_time DESC 
                LIMIT 15
            """)).fetchall()
            
            for file_path, sessions, total_time, last_worked in file_stats:
                hours = total_time / 3600
                print(f"{file_path:40} | {hours:5.2f}h | {sessions:3d} sessions | {last_worked.date()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    query_database()
    print("\n" + "="*50)
    custom_query("today")
    print("\n" + "="*50)
    custom_query("files")








