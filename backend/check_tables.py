#!/usr/bin/env python3
"""
Script to check the database tables and their structure
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

def check_database_tables():
    """Check what tables exist and their structure"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return
    
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        print("🔍 Checking Database Tables...")
        print("=" * 50)
        
        # Get all table names
        tables = inspector.get_table_names()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        print("\n📋 Table Structures:")
        print("=" * 50)
        
        # Check users table structure
        if 'users' in tables:
            print("\n👤 USERS table columns:")
            columns = inspector.get_columns('users')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} {'(Primary Key)' if col.get('primary_key') else ''}")
        
        # Check activity_records table structure
        if 'activity_records' in tables:
            print("\n📊 ACTIVITY_RECORDS table columns:")
            columns = inspector.get_columns('activity_records')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} {'(Primary Key)' if col.get('primary_key') else ''}")
        else:
            print("\n❌ ACTIVITY_RECORDS table not found - this is needed for the timesheet app")
        
        # Test a simple query
        print("\n🧪 Testing Database Connection:")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as user_count FROM users"))
            user_count = result.fetchone()[0]
            print(f"✅ Connection successful! Found {user_count} users in database")
            
            # Check if our required columns exist in users table
            try:
                result = conn.execute(text("SELECT username, email FROM users LIMIT 1"))
                print("✅ Users table has username and email columns (compatible)")
            except Exception as e:
                print(f"❌ Users table structure issue: {e}")
                print("💡 The existing users table might not be compatible with our app")
        
        print("\n🎯 Recommendations:")
        if 'activity_records' not in tables:
            print("❌ Missing activity_records table - run the setup again")
        if 'users' in tables:
            print("✅ Users table exists - check if structure is compatible above")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database_tables()








