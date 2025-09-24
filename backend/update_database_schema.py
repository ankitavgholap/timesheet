#!/usr/bin/env python3
"""
Quick script to update database schema for developer registration
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment
load_dotenv('.env.local')  # or .env.production for production
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Connecting to database: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("✅ Connected to database successfully!")
        
        # Add new columns for developer registration
        updates = [
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45) DEFAULT '127.0.0.1'
            """,
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS activitywatch_port INTEGER DEFAULT 5600
            """,
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS hostname VARCHAR(255) DEFAULT 'unknown'
            """,
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS browser_info VARCHAR(255)
            """,
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS activitywatch_status VARCHAR(50) DEFAULT 'unknown'
            """,
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS last_sync TIMESTAMP WITH TIME ZONE
            """,
            """
            ALTER TABLE developers 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            """
        ]
        
        for i, update in enumerate(updates, 1):
            try:
                conn.execute(text(update))
                print(f"✅ Update {i}/7 completed")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️  Update {i}/7 - Column already exists, skipping")
                else:
                    print(f"❌ Update {i}/7 failed: {e}")
        
        # Commit all changes
        conn.commit()
        print("🎉 All database updates completed!")
        
        # Verify the changes
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'developers'"))
        columns = [row[0] for row in result]
        print(f"\n📋 Current developers table columns:")
        for col in sorted(columns):
            print(f"   - {col}")
            
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Make sure PostgreSQL is running")
    print("   2. Check your .env.local file has correct DATABASE_URL")
    print("   3. Verify your database credentials")
