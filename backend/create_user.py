#!/usr/bin/env python3
"""
Simple script to create a test user
"""
import os
import sys
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import models
from database import engine
import crud
from schemas import UserCreate

load_dotenv()

def create_test_user():
    """Create a test user for the application"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = crud.get_user_by_username(db, "admin")
        if existing_user:
            print(f"✅ User 'admin' already exists (ID: {existing_user.id})")
            return existing_user
        
        # Create new user
        print("👤 Creating test user...")
        user_data = UserCreate(
            username="admin",
            email="admin@timesheet.com",
            password="admin123"
        )
        
        user = crud.create_user(db, user_data)
        print(f"✅ Test user created successfully!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Password: admin123")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating Test User for Timesheet Application")
    print("=" * 50)
    
    user = create_test_user()
    if user:
        print("\n🎉 Ready to start the application!")
        print("\nLogin credentials:")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("\n❌ Failed to create test user")








