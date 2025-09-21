#!/usr/bin/env python3
"""
Simple test script to run from the backend directory
"""

def test_imports():
    print("🔧 Testing imports from backend directory...")
    
    try:
        print("1. Testing dotenv...", end=" ")
        from dotenv import load_dotenv
        print("✅")
        
        print("2. Testing database.py...", end=" ")
        from database import engine, Base
        print("✅")
        
        print("3. Testing models.py...", end=" ")
        from models import User, ActivityRecord
        print("✅")
        
        print("4. Testing stateless_webhook.py...", end=" ")
        from stateless_webhook import validate_stateless_token
        print("✅")
        
        print("5. Testing database connection...", end=" ")
        conn = engine.connect()
        conn.close()
        print("✅")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()
