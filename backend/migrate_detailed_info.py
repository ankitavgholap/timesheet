#!/usr/bin/env python3
"""
Migration script to add detailed information columns to activity_records table
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    """Add new columns for detailed activity tracking"""
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                print("🔄 Adding new columns to activity_records table...")
                
                # Add new columns
                new_columns = [
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS file_path TEXT",
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS database_connection VARCHAR(255)",
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS specific_process VARCHAR(255)",
                    "ALTER TABLE activity_records ADD COLUMN IF NOT EXISTS detailed_activity TEXT"
                ]
                
                for sql in new_columns:
                    print(f"  Executing: {sql}")
                    conn.execute(text(sql))
                
                trans.commit()
                print("✅ Database migration completed successfully!")
                
                # Verify columns were added
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'activity_records' 
                    AND column_name IN ('file_path', 'database_connection', 'specific_process', 'detailed_activity')
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
    print("Database Migration: Adding Detailed Activity Tracking")
    print("=" * 60)
    
    if migrate_database():
        print("\n🎉 Migration completed successfully!")
        print("\nNew features available:")
        print("• 📁 File path tracking for IDEs")
        print("• 🗄️ Database connection details")
        print("• ⚙️ Specific process information")
        print("• 📋 Enhanced activity descriptions")
        print("\nRestart your backend server to use the new features!")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")
