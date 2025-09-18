#!/usr/bin/env python3
"""
Check what data is actually stored in the database
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import models
from database import SessionLocal

load_dotenv()

def check_database_data():
    """Check what's actually stored in the database"""
    db = SessionLocal()
    
    try:
        print("🔍 Checking Database Data...")
        print("=" * 50)
        
        # Get recent activity records
        recent_activities = db.query(models.ActivityRecord).order_by(
            models.ActivityRecord.timestamp.desc()
        ).limit(10).all()
        
        print(f"Found {len(recent_activities)} recent activities:")
        print()
        
        for i, activity in enumerate(recent_activities, 1):
            print(f"{i:2d}. {activity.application_name} | {activity.duration:.1f}s")
            print(f"    Window Title: {activity.window_title}")
            print(f"    Category: {activity.category}")
            print(f"    URL: {activity.url}")
            print(f"    File Path: {activity.file_path}")
            print(f"    Database Connection: {activity.database_connection}")
            print(f"    Specific Process: {activity.specific_process}")
            print(f"    Detailed Activity: {activity.detailed_activity}")
            print(f"    Timestamp: {activity.timestamp}")
            print()
        
        # Check if new columns exist
        print("🔍 Checking Database Schema...")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'activity_records'
            ORDER BY column_name
        """))
        
        columns = result.fetchall()
        print("Activity Records table columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_data()
