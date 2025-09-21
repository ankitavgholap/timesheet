#!/usr/bin/env python3
"""
Test script to run directly from backend directory
"""

import os
from dotenv import load_dotenv

def test_backend():
    print("🔧 Backend Test (from backend directory)")
    print("=" * 45)
    
    # Check current directory
    print("Current directory:", os.getcwd())
    
    # Check .env file
    env_exists = os.path.exists('.env')
    print(f".env file exists: {'✅ Yes' if env_exists else '❌ No'}")
    
    if env_exists:
        # Try to read .env content (first 3 lines)
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()[:3]
                print("First 3 lines of .env:")
                for i, line in enumerate(lines, 1):
                    # Don't show full secrets, just indicate they exist
                    if '=' in line:
                        key = line.split('=')[0]
                        print(f"  {i}. {key}=...")
                    else:
                        print(f"  {i}. {line.strip()}")
        except Exception as e:
            print(f"Error reading .env: {e}")
    
    # Load environment variables
    print("\n🔧 Loading environment variables...")
    load_dotenv()
    
    # Check required variables
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'MASTER_SECRET']
    for var in required_vars:
        value = os.getenv(var)
        status = f"✅ Set ({len(value)} chars)" if value else "❌ Missing"
        print(f"{var}: {status}")
    
    # Test imports
    print("\n🧪 Testing imports...")
    
    try:
        from database import engine, Base
        print("✅ Database import: Success")
        
        # Test database connection
        conn = engine.connect()
        conn.close()
        print("✅ Database connection: Success")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    try:
        from models import User, ActivityRecord
        print("✅ Models import: Success")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from stateless_webhook import validate_stateless_token
        print("✅ Stateless webhook import: Success")
    except Exception as e:
        print(f"❌ Webhook import failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Backend is ready.")
    return True

if __name__ == "__main__":
    test_backend()
