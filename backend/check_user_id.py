#!/usr/bin/env python3
"""
Check what user IDs exist in the database
"""
from database import SessionLocal
import models

def check_users():
    db = SessionLocal()
    
    try:
        print("👥 Checking Users in Database")
        print("=" * 30)
        
        users = db.query(models.User).all()
        
        if not users:
            print("❌ No users found in database")
            return
        
        for user in users:
            print(f"User ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            
            # Check activity count for this user
            activity_count = db.query(models.ActivityRecord).filter(
                models.ActivityRecord.user_id == user.id
            ).count()
            print(f"Activities: {activity_count}")
            print("-" * 20)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()








