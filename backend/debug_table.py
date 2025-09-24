#!/usr/bin/env python3
"""
Debug your developers table and create a token
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import secrets

# Load environment
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL")

print("🔍 Debugging developers table...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check table structure
        print("📋 Checking developers table structure:")
        
        columns_query = text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'developers'
            ORDER BY ordinal_position
        """)
        
        result = conn.execute(columns_query)
        columns = result.fetchall()
        
        if not columns:
            print("❌ No 'developers' table found!")
            exit(1)
        
        print("Available columns:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'} - Default: {col[3]}")
        
        # Check existing data
        count_query = text("SELECT COUNT(*) FROM developers")
        count_result = conn.execute(count_query)
        total_devs = count_result.scalar()
        
        print(f"\n📊 Current developers in table: {total_devs}")
        
        if total_devs > 0:
            sample_query = text("SELECT id, name, email, active, created_at FROM developers LIMIT 3")
            sample_result = conn.execute(sample_query)
            sample_data = sample_result.fetchall()
            
            print("Sample data:")
            for row in sample_data:
                print(f"   - ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Active: {row[3]}")
        
        # Create a test token
        print(f"\n🔑 Creating test token...")
        token = f"AWToken_{secrets.token_urlsafe(32)}"
        
        print("=" * 60)
        print("🎉 TEST REGISTRATION DATA:")
        print("=" * 60)
        print(f"Name: Test Developer")
        print(f"Token: {token}")
        print("=" * 60)
        print("📋 Instructions:")
        print("1. Start your backend: python main.py")
        print("2. Visit: http://localhost:8000/register-developer")
        print("3. Enter the name and token above")
        print("4. Try registration!")
        
except Exception as e:
    print(f"❌ Error: {e}")
