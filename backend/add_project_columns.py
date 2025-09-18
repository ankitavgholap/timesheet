#!/usr/bin/env python3
"""
Migration script to add project information columns to activity_records table
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def add_project_columns():
    """Add project information columns to activity_records table"""
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                print("🔄 Adding project information columns to activity_records table...")
                
                # Add new project columns
                new_columns = [
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS project_name VARCHAR(255)",
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS project_type VARCHAR(100)",
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS project_file VARCHAR(255)"
                ]
                
                for sql in new_columns:
                    print(f"  Executing: {sql}")
                    conn.execute(text(sql))
                
                # Create index on project_name for better query performance
                index_sql = "CREATE INDEX IF NOT EXISTS idx_activity_records_project_name ON activity_records(project_name)"
                print(f"  Executing: {index_sql}")
                conn.execute(text(index_sql))
                
                trans.commit()
                print("✅ Project columns added successfully!")
                
                # Verify columns were added
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'activity_records' 
                    AND column_name IN ('project_name', 'project_type', 'project_file')
                    ORDER BY column_name
                """))
                
                added_columns = [row[0] for row in result.fetchall()]
                print(f"✅ Verified new columns: {added_columns}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error during migration: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting project columns migration...")
    success = add_project_columns()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
