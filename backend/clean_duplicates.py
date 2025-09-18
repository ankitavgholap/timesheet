#!/usr/bin/env python3
"""
Clean up duplicate activity records in the database
"""
import os
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import models
from database import SessionLocal

load_dotenv()

def clean_duplicates():
    """Remove duplicate activity records, keeping only the first occurrence"""
    db = SessionLocal()
    
    try:
        print("🧹 Cleaning Duplicate Activity Records...")
        print("=" * 50)
        
        # Count total records before cleanup
        total_before = db.query(models.ActivityRecord).count()
        print(f"📊 Total records before cleanup: {total_before}")
        
        # Find duplicates using raw SQL for better performance
        duplicate_query = text("""
            WITH duplicates AS (
                SELECT id, 
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, application_name, window_title, timestamp, duration 
                           ORDER BY id
                       ) as row_num
                FROM activity_records
            )
            SELECT id FROM duplicates WHERE row_num > 1
        """)
        
        result = db.execute(duplicate_query)
        duplicate_ids = [row[0] for row in result.fetchall()]
        
        print(f"🔍 Found {len(duplicate_ids)} duplicate records to delete")
        
        if duplicate_ids:
            # Delete duplicates in batches to avoid memory issues
            batch_size = 1000
            deleted_count = 0
            
            for i in range(0, len(duplicate_ids), batch_size):
                batch_ids = duplicate_ids[i:i + batch_size]
                
                # Delete this batch
                delete_query = text("""
                    DELETE FROM activity_records 
                    WHERE id = ANY(:ids)
                """)
                
                db.execute(delete_query, {"ids": batch_ids})
                db.commit()
                
                deleted_count += len(batch_ids)
                print(f"🗑️  Deleted batch {i//batch_size + 1}: {deleted_count}/{len(duplicate_ids)} records")
            
            print(f"✅ Successfully deleted {deleted_count} duplicate records")
        else:
            print("✅ No duplicates found")
        
        # Count total records after cleanup
        total_after = db.query(models.ActivityRecord).count()
        print(f"📊 Total records after cleanup: {total_after}")
        print(f"💾 Space saved: {total_before - total_after} records")
        
        # Recalculate today's total time
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(hour=23, minute=59, second=59)
        
        new_total = db.query(func.sum(models.ActivityRecord.duration)).filter(
            models.ActivityRecord.timestamp >= today,
            models.ActivityRecord.timestamp <= tomorrow
        ).scalar() or 0
        
        print(f"⏱️  Today's corrected total time: {new_total:.2f} seconds = {new_total/3600:.2f} hours")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_duplicates()








