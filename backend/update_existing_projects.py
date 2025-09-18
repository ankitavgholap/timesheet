#!/usr/bin/env python3
"""
Update existing activity records with project information
"""
from database import SessionLocal
import models
from project_extractor import extract_project_info
from sqlalchemy import and_

def update_existing_records():
    """Update existing activity records with project information"""
    db = SessionLocal()
    
    try:
        print("🔄 Updating existing activity records with project information...")
        
        # Get all records without project information
        records_to_update = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.project_name.is_(None)
        ).all()
        
        print(f"📊 Found {len(records_to_update)} records to update")
        
        updated_count = 0
        batch_size = 100
        
        for i, record in enumerate(records_to_update):
            # Create activity data dict for project extraction
            activity_data = {
                "application_name": record.application_name,
                "window_title": record.window_title,
                "file_path": record.file_path,
                "category": record.category,
                "url": record.url,
                "database_connection": record.database_connection,
                "specific_process": record.specific_process,
                "detailed_activity": record.detailed_activity
            }
            
            # Extract project information
            project_info = extract_project_info(activity_data)
            
            # Update the record
            record.project_name = project_info.get("project_name")
            record.project_type = project_info.get("project_type") 
            record.project_file = project_info.get("project_file")
            
            updated_count += 1
            
            # Commit in batches for better performance
            if (i + 1) % batch_size == 0:
                db.commit()
                print(f"  ✅ Updated {i + 1}/{len(records_to_update)} records...")
        
        # Final commit
        db.commit()
        
        print(f"🎉 Successfully updated {updated_count} records with project information!")
        
        # Show some statistics
        project_stats = db.execute("""
            SELECT project_name, project_type, COUNT(*) as count
            FROM activity_records 
            WHERE project_name IS NOT NULL
            GROUP BY project_name, project_type
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        
        print("\n📈 Top 10 Projects:")
        print("-" * 50)
        for project_name, project_type, count in project_stats:
            print(f"{project_name:30} | {project_type:15} | {count:4d} activities")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating records: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting project information update...")
    success = update_existing_records()
    
    if success:
        print("✅ Update completed successfully!")
    else:
        print("💥 Update failed!")
