#!/usr/bin/env python3
"""
Debug total time calculation to find why working hours are incorrect
"""
import os
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import models
from database import SessionLocal
from datetime import datetime, timezone

load_dotenv()

def debug_total_time():
    """Debug total time calculation"""
    db = SessionLocal()
    
    try:
        print("🔍 Debugging Total Time Calculation...")
        print("=" * 60)
        
        # Get today's date range
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(hour=23, minute=59, second=59)
        
        print(f"Date range: {today} to {tomorrow}")
        print()
        
        # 1. Check total records for today
        total_records = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).count()
        print(f"📊 Total activity records for today: {total_records}")
        
        # 2. Check raw sum of all durations
        raw_total = db.query(func.sum(models.ActivityRecord.duration)).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).scalar() or 0
        print(f"⏱️  Raw total duration (all records): {raw_total:.2f} seconds = {raw_total/3600:.2f} hours")
        
        # 3. Check grouped sum (what the API returns)
        grouped_results = db.query(
            models.ActivityRecord.application_name,
            func.sum(models.ActivityRecord.duration).label('total_duration')
        ).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).group_by(
            models.ActivityRecord.application_name
        ).all()
        
        grouped_total = sum(result.total_duration for result in grouped_results)
        print(f"📈 Grouped total duration (API method): {grouped_total:.2f} seconds = {grouped_total/3600:.2f} hours")
        
        print()
        print("🔍 Breakdown by Application:")
        print("-" * 40)
        for result in grouped_results:
            hours = result.total_duration / 3600
            print(f"{result.application_name:20} | {result.total_duration:8.1f}s | {hours:6.2f}h")
        
        # 4. Check for duplicates
        print()
        print("🔍 Checking for Duplicate Records...")
        print("-" * 40)
        
        duplicate_check = db.query(
            models.ActivityRecord.application_name,
            models.ActivityRecord.window_title,
            models.ActivityRecord.timestamp,
            func.count().label('count')
        ).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).group_by(
            models.ActivityRecord.application_name,
            models.ActivityRecord.window_title,
            models.ActivityRecord.timestamp
        ).having(func.count() > 1).all()
        
        if duplicate_check:
            print(f"⚠️  Found {len(duplicate_check)} duplicate record groups:")
            for dup in duplicate_check:
                print(f"   {dup.application_name} | {dup.window_title[:30]}... | {dup.count} duplicates")
        else:
            print("✅ No duplicate records found")
        
        # 5. Check individual record durations
        print()
        print("🔍 Sample Individual Records:")
        print("-" * 60)
        sample_records = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).order_by(models.ActivityRecord.duration.desc()).limit(10).all()
        
        for record in sample_records:
            print(f"{record.application_name:15} | {record.duration:8.1f}s | {record.window_title[:30]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_total_time()








