#!/usr/bin/env python3
"""
Check project extraction results
"""
from database import SessionLocal
import models
from sqlalchemy import text

def check_projects():
    """Check project extraction results"""
    db = SessionLocal()
    
    try:
        print("📊 PROJECT EXTRACTION RESULTS")
        print("=" * 50)
        
        # Get project statistics
        result = db.execute(text("""
            SELECT project_name, project_type, COUNT(*) as count, 
                   SUM(duration)/3600 as total_hours
            FROM activity_records 
            WHERE project_name IS NOT NULL
            GROUP BY project_name, project_type
            ORDER BY count DESC
            LIMIT 20
        """)).fetchall()
        
        print(f"{'Project Name':<30} | {'Type':<15} | {'Activities':<10} | {'Hours':<8}")
        print("-" * 70)
        
        total_projects = 0
        for project_name, project_type, count, hours in result:
            total_projects += 1
            print(f"{project_name[:29]:<30} | {project_type:<15} | {count:<10} | {hours:<8.2f}")
        
        print(f"\n🎯 Total unique projects: {total_projects}")
        
        # Check records without project info
        no_project_count = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.project_name.is_(None)
        ).count()
        
        total_records = db.query(models.ActivityRecord).count()
        
        print(f"📈 Records with project info: {total_records - no_project_count}/{total_records}")
        print(f"📊 Coverage: {((total_records - no_project_count) / total_records * 100):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    check_projects()
