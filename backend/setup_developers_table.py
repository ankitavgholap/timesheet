#!/usr/bin/env python3
"""
Complete Solution: Create/Update developers table and fix registration
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

# Load environment
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL")

print("🔧 Setting up developers table properly...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # First, let's see what tables exist
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        result = conn.execute(tables_query)
        existing_tables = [row[0] for row in result]
        print(f"📋 Existing tables: {existing_tables}")
        
        # Check if developers table exists and its structure
        if 'developers' in existing_tables:
            print("\n🔍 Checking current developers table structure...")
            
            columns_query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'developers'
                ORDER BY ordinal_position
            """)
            
            result = conn.execute(columns_query)
            columns = result.fetchall()
            
            print("Current columns:")
            for col in columns:
                print(f"   - {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        # Create/update the developers table to match the model
        print("\n🔨 Creating/updating developers table to match your model...")
        
        # Drop and recreate table to match your exact model
        drop_table = text("DROP TABLE IF EXISTS developers CASCADE")
        conn.execute(drop_table)
        
        create_table = text("""
            CREATE TABLE developers (
                id SERIAL PRIMARY KEY,
                developer_id VARCHAR UNIQUE,
                name VARCHAR,
                email VARCHAR,
                active BOOLEAN DEFAULT TRUE,
                api_token VARCHAR UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_sync TIMESTAMP WITH TIME ZONE
            )
        """)
        
        conn.execute(create_table)
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_developers_developer_id ON developers (developer_id)",
            "CREATE INDEX IF NOT EXISTS ix_developers_api_token ON developers (api_token)"
        ]
        
        for idx in indexes:
            conn.execute(text(idx))
        
        conn.commit()
        
        print("✅ Developers table created successfully!")
        
        # Verify the new structure
        print("\n📋 New table structure:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'developers'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        for col in columns:
            print(f"   - {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        print("\n🎉 Database setup complete!")
        
except Exception as e:
    print(f"❌ Error: {e}")
