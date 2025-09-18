#!/usr/bin/env python3
"""
Script to fix foreign key constraints after renaming users table
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import models
from database import Base

load_dotenv()

def fix_foreign_keys():
    """Fix foreign key constraints in activity_records table"""
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                print("🔄 Dropping activity_records table...")
                conn.execute(text("DROP TABLE IF EXISTS activity_records CASCADE"))
                
                print("✅ Activity_records table dropped")
                trans.commit()
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error dropping table: {e}")
                return False
        
        # Recreate the activity_records table with correct foreign keys
        print("🆕 Creating activity_records table with correct foreign keys...")
        models.ActivityRecord.__table__.create(engine)
        
        print("✅ Activity_records table recreated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Foreign Key Fix for Activity Records Table")
    print("=" * 50)
    
    if fix_foreign_keys():
        print("\n🎉 Foreign keys fixed successfully!")
        print("You can now create users and activity records.")
    else:
        print("\n❌ Failed to fix foreign keys")
