#!/usr/bin/env python3
"""
Fix developers table structure
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL")

print("🔧 Fixing developers table structure...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check current table structure
        print("📋 Checking current developers table structure...")
        
        try:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'developers'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            print("Current columns:")
            for col in columns:
                print(f"   - {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            
        except Exception as e:
            print(f"Could not check table structure: {e}")
        
        # Add missing columns
        print("\n🔨 Adding missing columns...")
        
        updates = [
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS developer_id VARCHAR(255)",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45) DEFAULT '127.0.0.1'",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS activitywatch_port INTEGER DEFAULT 5600",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS hostname VARCHAR(255) DEFAULT 'unknown'",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS browser_info VARCHAR(255)",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS activitywatch_status VARCHAR(50) DEFAULT 'unknown'",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS last_sync TIMESTAMP WITH TIME ZONE",
            "ALTER TABLE developers ADD COLUMN IF NOT EXISTS api_token VARCHAR(255)"
        ]
        
        for i, update in enumerate(updates, 1):
            try:
                conn.execute(text(update))
                print(f"✅ Update {i}/{len(updates)}: Added column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️  Update {i}/{len(updates)}: Column already exists")
                else:
                    print(f"❌ Update {i}/{len(updates)}: {e}")
        
        # Create indexes
        print("\n📇 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_developers_developer_id ON developers (developer_id)",
            "CREATE INDEX IF NOT EXISTS idx_developers_active ON developers (active)",
            "CREATE INDEX IF NOT EXISTS idx_developers_api_token ON developers (api_token)"
        ]
        
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                print("✅ Index created")
            except Exception as e:
                print(f"⚠️  Index: {e}")
        
        # Commit all changes
        conn.commit()
        
        # Verify the updates
        print("\n🔍 Verifying updated table structure...")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'developers'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        
        print("Updated table structure:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        print("\n🎉 Developers table structure updated successfully!")
        
except Exception as e:
    print(f"❌ Error updating table: {e}")
