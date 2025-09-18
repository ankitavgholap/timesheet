#!/usr/bin/env python3
"""
Database Inspector - Check database values and see where data is stored
"""
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import models
from database import SessionLocal
from datetime import datetime, timezone

load_dotenv()

def inspect_database():
    """Comprehensive database inspection"""
    db = SessionLocal()
    
    try:
        print("🗄️ DATABASE INSPECTION")
        print("=" * 60)
        
        # 1. Database Connection Info
        print("📡 CONNECTION INFO:")
        print("-" * 30)
        database_url = os.getenv("DATABASE_URL", "Not found")
        print(f"Database URL: {database_url}")
        
        # Get database engine info
        engine = db.get_bind()
        print(f"Database Type: {engine.dialect.name}")
        print(f"Database Driver: {engine.dialect.driver}")
        print()
        
        # 2. Tables Overview
        print("📊 TABLES OVERVIEW:")
        print("-" * 30)
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table_name in tables:
            # Get table info
            columns = inspector.get_columns(table_name)
            row_count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            print(f"Table: {table_name}")
            print(f"  Rows: {row_count}")
            print(f"  Columns: {len(columns)}")
            
            # Show column details
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                print(f"    • {col['name']}: {col['type']} {nullable}{default}")
            print()
        
        # 3. Users Table Data
        print("👥 USERS TABLE:")
        print("-" * 30)
        
        users = db.query(models.User).all()
        if users:
            for user in users:
                print(f"ID: {user.id}")
                print(f"  Username: {user.username}")
                print(f"  Email: {user.email}")
                print(f"  Created: {user.created_at if hasattr(user, 'created_at') else 'N/A'}")
                
                # Count activities for this user
                activity_count = db.query(models.ActivityRecord).filter(
                    models.ActivityRecord.user_id == user.id
                ).count()
                print(f"  Total Activities: {activity_count}")
                print()
        else:
            print("No users found!")
        
        # 4. Activity Records Sample
        print("📋 ACTIVITY RECORDS SAMPLE (Latest 5):")
        print("-" * 50)
        
        recent_activities = db.query(models.ActivityRecord).order_by(
            models.ActivityRecord.timestamp.desc()
        ).limit(5).all()
        
        if recent_activities:
            for i, activity in enumerate(recent_activities, 1):
                print(f"{i}. ID: {activity.id}")
                print(f"   User ID: {activity.user_id}")
                print(f"   App: {activity.application_name}")
                print(f"   Title: {activity.window_title[:50]}...")
                print(f"   Category: {activity.category}")
                print(f"   Duration: {activity.duration:.1f}s")
                print(f"   Timestamp: {activity.timestamp}")
                print(f"   URL: {activity.url}")
                print(f"   File Path: {activity.file_path}")
                print(f"   Detailed Activity: {activity.detailed_activity}")
                print()
        else:
            print("No activity records found!")
        
        # 5. Database Statistics
        print("📈 DATABASE STATISTICS:")
        print("-" * 30)
        
        # Total records
        total_activities = db.query(models.ActivityRecord).count()
        total_users = db.query(models.User).count()
        
        print(f"Total Users: {total_users}")
        print(f"Total Activity Records: {total_activities}")
        
        if total_activities > 0:
            # Date range
            first_activity = db.query(models.ActivityRecord).order_by(
                models.ActivityRecord.timestamp.asc()
            ).first()
            last_activity = db.query(models.ActivityRecord).order_by(
                models.ActivityRecord.timestamp.desc()
            ).first()
            
            print(f"First Activity: {first_activity.timestamp}")
            print(f"Last Activity: {last_activity.timestamp}")
            
            # Total time tracked
            total_duration = db.query(
                models.ActivityRecord
            ).with_entities(
                db.func.sum(models.ActivityRecord.duration)
            ).scalar() or 0
            
            total_hours = total_duration / 3600
            print(f"Total Time Tracked: {total_hours:.2f} hours")
            
            # Categories breakdown
            print("\nCategories:")
            category_stats = db.execute(text("""
                SELECT category, 
                       COUNT(*) as count,
                       SUM(duration) as total_duration
                FROM activity_records 
                GROUP BY category 
                ORDER BY total_duration DESC
            """)).fetchall()
            
            for cat, count, duration in category_stats:
                hours = duration / 3600 if duration else 0
                print(f"  • {cat}: {count} records, {hours:.2f}h")
        
        print()
        
        # 6. How to Query Data
        print("🔍 HOW TO QUERY YOUR DATA:")
        print("-" * 30)
        print("You can query your data using:")
        print()
        print("1. Direct SQL queries:")
        print("   SELECT * FROM users;")
        print("   SELECT * FROM activity_records WHERE user_id = 2;")
        print("   SELECT category, SUM(duration) FROM activity_records GROUP BY category;")
        print()
        print("2. Python scripts (like this one):")
        print("   from database import SessionLocal")
        print("   import models")
        print("   db = SessionLocal()")
        print("   activities = db.query(models.ActivityRecord).all()")
        print()
        print("3. Database tools:")
        print("   - DataGrip (you already have this!)")
        print("   - pgAdmin for PostgreSQL")
        print("   - DBeaver (free)")
        print()
        
        # 7. File Locations
        print("📁 FILE LOCATIONS:")
        print("-" * 30)
        print("Database Models: backend/models.py")
        print("Database Config: backend/database.py")
        print("Environment File: .env (contains DATABASE_URL)")
        print("CRUD Operations: backend/crud.py")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def show_specific_user_data(user_id: int = 2):
    """Show detailed data for a specific user"""
    db = SessionLocal()
    
    try:
        print(f"\n👤 DETAILED DATA FOR USER ID: {user_id}")
        print("=" * 50)
        
        # User info
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            print(f"❌ User with ID {user_id} not found!")
            return
        
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print()
        
        # Recent activities
        activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.user_id == user_id
        ).order_by(models.ActivityRecord.timestamp.desc()).limit(10).all()
        
        print(f"📋 RECENT ACTIVITIES (Last 10):")
        print("-" * 40)
        
        for i, activity in enumerate(activities, 1):
            print(f"{i:2d}. {activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    App: {activity.application_name}")
            print(f"    Title: {activity.window_title}")
            print(f"    Category: {activity.category}")
            print(f"    Duration: {activity.duration:.1f}s")
            if activity.url:
                print(f"    URL: {activity.url}")
            if activity.file_path:
                print(f"    File: {activity.file_path}")
            print()
        
        # Today's summary
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(hour=23, minute=59, second=59)
        
        today_activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.user_id == user_id,
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).all()
        
        if today_activities:
            total_time = sum(a.duration for a in today_activities)
            print(f"📅 TODAY'S SUMMARY:")
            print("-" * 20)
            print(f"Activities: {len(today_activities)}")
            print(f"Total Time: {total_time/3600:.2f} hours")
            
            # Category breakdown for today
            categories = {}
            for activity in today_activities:
                cat = activity.category
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += activity.duration
            
            print("Categories:")
            for cat, duration in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                hours = duration / 3600
                print(f"  • {cat}: {hours:.2f}h")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_database()
    show_specific_user_data(2)  # Show data for admin user








