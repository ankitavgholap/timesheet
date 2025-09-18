#!/usr/bin/env python3
"""
Script to fix the users table for the timesheet application
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import models
from database import Base

load_dotenv()

def fix_users_table():
    """Rename existing users table and create our own"""
    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                print("🔄 Renaming existing users table to users_backup...")
                conn.execute(text("ALTER TABLE users RENAME TO users_backup"))
                
                print("✅ Existing users table backed up as 'users_backup'")
                
                # Commit the rename
                trans.commit()
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error renaming table: {e}")
                return False
        
        # Now create our users table
        print("🆕 Creating new users table for timesheet app...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ New users table created successfully!")
        print("\n🎯 Next steps:")
        print("1. Your original users data is safe in 'users_backup' table")
        print("2. You can now register new users for the timesheet app")
        print("3. If needed, you can migrate data from users_backup later")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Users Table Fix for Timesheet Application")
    print("=" * 50)
    
    response = input("This will rename your existing 'users' table to 'users_backup' and create a new one for the timesheet app. Continue? (y/N): ")
    
    if response.lower() == 'y':
        if fix_users_table():
            print("\n🎉 Users table fixed successfully!")
        else:
            print("\n❌ Failed to fix users table")
    else:
        print("Operation cancelled.")
