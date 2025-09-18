#!/usr/bin/env python3
"""
View all saved activity data from the database
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import models
from database import SessionLocal
from datetime import datetime, timezone

load_dotenv()

def view_saved_data():
    """View all saved activity data"""
    db = SessionLocal()
    
    try:
        print("📊 Your Saved Activity Data")
        print("=" * 60)
        
        # Get total records
        total_records = db.query(models.ActivityRecord).count()
        print(f"Total saved records: {total_records}")
        
        # Get date range of saved data
        first_record = db.query(models.ActivityRecord).order_by(models.ActivityRecord.timestamp.asc()).first()
        last_record = db.query(models.ActivityRecord).order_by(models.ActivityRecord.timestamp.desc()).first()
        
        if first_record and last_record:
            print(f"Date range: {first_record.timestamp.date()} to {last_record.timestamp.date()}")
        
        print()
        print("📋 Recent Activity Records:")
        print("-" * 60)
        
        # Get recent records
        recent_records = db.query(models.ActivityRecord).order_by(
            models.ActivityRecord.timestamp.desc()
        ).limit(20).all()
        
        for i, record in enumerate(recent_records, 1):
            hours = record.duration / 3600
            print(f"{i:2d}. {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    App: {record.application_name}")
            print(f"    Title: {record.window_title}")
            print(f"    Category: {record.category}")
            print(f"    Duration: {record.duration:.1f}s ({hours:.2f}h)")
            if record.url:
                print(f"    URL: {record.url}")
            if record.file_path:
                print(f"    File: {record.file_path}")
            print()
        
        # Summary by category
        print("📈 Summary by Category:")
        print("-" * 30)
        
        category_summary = db.execute(text("""
            SELECT category, 
                   COUNT(*) as record_count,
                   SUM(duration) as total_duration
            FROM activity_records 
            GROUP BY category 
            ORDER BY total_duration DESC
        """)).fetchall()
        
        for cat, count, duration in category_summary:
            hours = duration / 3600
            print(f"{cat:15} | {count:4d} records | {hours:6.2f} hours")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    view_saved_data()
