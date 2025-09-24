#!/usr/bin/env python3
"""
Check your current database setup and connection
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

print("🔍 Checking your database setup...")

# Check different environment files
env_files = ['.env.local', '.env.production', '.env']

for env_file in env_files:
    if os.path.exists(env_file):
        print(f"\n📁 Found {env_file}:")
        load_dotenv(env_file, override=True)
        database_url = os.getenv("DATABASE_URL")
        environment = os.getenv("ENVIRONMENT", "unknown")
        
        print(f"   Environment: {environment}")
        print(f"   Database URL: {database_url}")
        
        if database_url:
            try:
                engine = create_engine(database_url)
                with engine.connect() as conn:
                    # Test the connection
                    result = conn.execute(text("SELECT COUNT(*) FROM developers"))
                    count = result.scalar()
                    print(f"   ✅ Connection successful! Found {count} developers")
                    
                    # Check if table has required columns
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'developers'
                    """))
                    columns = [row[0] for row in result]
                    
                    required_columns = ['ip_address', 'activitywatch_port', 'hostname', 'browser_info']
                    missing_columns = [col for col in required_columns if col not in columns]
                    
                    if missing_columns:
                        print(f"   ⚠️  Missing columns: {missing_columns}")
                        print("   → Need to run database updates")
                    else:
                        print("   ✅ All required columns present")
                    
            except Exception as e:
                print(f"   ❌ Connection failed: {e}")

print(f"\n🏠 Current working directory: {os.getcwd()}")
print(f"📂 Available .env files: {[f for f in env_files if os.path.exists(f)]}")
