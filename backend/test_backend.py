#!/usr/bin/env python3
"""
Simple test to verify backend imports work correctly
Run this from the timesheet_new directory
"""

import sys
import os

def test_backend_imports():
    print("🔧 Testing Backend Imports")
    print("=" * 40)
    
    # Check if we're in the right directory
    backend_path = os.path.join(os.getcwd(), 'backend')
    if not os.path.exists(backend_path):
        print(f"❌ Backend directory not found at: {backend_path}")
        print("Please run this script from the timesheet_new directory")
        return False
    
    # Add backend to path
    sys.path.insert(0, backend_path)
    
    # Test each import step by step
    tests = [
        ("Testing dotenv", lambda: __import__('dotenv')),
        ("Testing database.py", lambda: __import__('database')),
        ("Testing models.py", lambda: __import__('models')),
        ("Testing stateless_webhook.py", lambda: __import__('stateless_webhook')),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"1. {test_name}...", end=" ")
            test_func()
            print("✅ Success")
        except Exception as e:
            print(f"❌ Failed: {e}")
            return False
    
    # Test database connection
    try:
        print("2. Testing database connection...", end=" ")
        from database import engine
        conn = engine.connect()
        conn.close()
        print("✅ Success")
    except Exception as e:
        print(f"❌ Failed: {e}")
        print(f"   Make sure your .env file has correct DATABASE_URL")
        return False
    
    # Test specific imports
    try:
        print("3. Testing specific model imports...", end=" ")
        from models import User, ActivityRecord
        print("✅ Success")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    try:
        print("4. Testing stateless webhook functions...", end=" ")
        from stateless_webhook import validate_stateless_token
        print("✅ Success")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    print("\n🎉 All imports working correctly!")
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n🔍 Checking Environment Configuration")
    print("=" * 40)
    
    env_path = os.path.join('backend', '.env')
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at: {env_path}")
        print("You need to create a .env file in the backend directory")
        return False
    
    print(f"✅ .env file found at: {env_path}")
    
    # Check required variables
    sys.path.insert(0, 'backend')
    try:
        from dotenv import load_dotenv
        import os as env_os
        
        load_dotenv(env_path)
        
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY', 
            'MASTER_SECRET'
        ]
        
        for var in required_vars:
            value = env_os.getenv(var)
            if value:
                print(f"✅ {var}: Set ({len(value)} chars)")
            else:
                print(f"❌ {var}: Missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking .env file: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Backend Import Test")
    print("=" * 50)
    
    # Check environment first
    if not check_env_file():
        print("\n💡 Create .env file first with these variables:")
        print("   DATABASE_URL=postgresql://user:pass@localhost:5432/timesheet")
        print("   SECRET_KEY=your-64-character-jwt-secret") 
        print("   MASTER_SECRET=your-32-character-master-secret")
        sys.exit(1)
    
    # Test imports
    if test_backend_imports():
        print("\n✅ Ready to start your application!")
        print("Next step: Update main.py and start the server")
    else:
        print("\n❌ Fix the errors above before continuing")
        sys.exit(1)
