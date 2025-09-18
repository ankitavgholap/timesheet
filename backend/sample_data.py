#!/usr/bin/env python3
"""
Sample data generator for testing the timesheet application
This creates fake activity data when ActivityWatch is not available
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import crud

# Sample applications and their categories
SAMPLE_APPS = {
    'browser': [
        ('Google Chrome', ['https://github.com', 'https://stackoverflow.com', 'https://google.com', 'https://youtube.com']),
        ('Mozilla Firefox', ['https://developer.mozilla.org', 'https://reddit.com', 'https://twitter.com']),
        ('Microsoft Edge', ['https://docs.microsoft.com', 'https://linkedin.com', 'https://outlook.com']),
    ],
    'development': [
        ('Visual Studio Code', []),
        ('PyCharm', []),
        ('IntelliJ IDEA', []),
        ('Cursor', []),
        ('Sublime Text', []),
    ],
    'productivity': [
        ('Microsoft Word', []),
        ('Microsoft Excel', []),
        ('Slack', []),
        ('Microsoft Teams', []),
        ('Notion', []),
        ('Obsidian', []),
    ],
    'entertainment': [
        ('Spotify', []),
        ('YouTube Music', []),
        ('Netflix', []),
        ('VLC Media Player', []),
    ],
    'system': [
        ('Windows Explorer', []),
        ('Command Prompt', []),
        ('PowerShell', []),
        ('Task Manager', []),
    ]
}

def generate_sample_data(user_id: int, days: int = 7):
    """Generate sample activity data for testing"""
    db = SessionLocal()
    
    try:
        # Clear existing data for this user
        db.query(models.ActivityRecord).filter(models.ActivityRecord.user_id == user_id).delete()
        db.commit()
        
        activities = []
        
        for day in range(days):
            current_date = datetime.now() - timedelta(days=day)
            
            # Generate 20-50 activities per day
            num_activities = random.randint(20, 50)
            
            for _ in range(num_activities):
                # Pick random category and app
                category = random.choice(list(SAMPLE_APPS.keys()))
                app_name, urls = random.choice(SAMPLE_APPS[category])
                
                # Generate random duration (30 seconds to 2 hours)
                duration = random.randint(30, 7200)
                
                # Random timestamp during the day
                hour = random.randint(8, 22)  # Working hours
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = current_date.replace(hour=hour, minute=minute, second=second)
                
                # Generate window title and URL
                window_title = f"{app_name}"
                url = None
                
                if category == 'browser' and urls:
                    url = random.choice(urls)
                    window_title = f"Some Page Title - {url}"
                elif category == 'development':
                    files = ['main.py', 'app.js', 'index.html', 'style.css', 'README.md']
                    window_title = f"{random.choice(files)} - {app_name}"
                elif category == 'productivity':
                    docs = ['Document1.docx', 'Presentation.pptx', 'Spreadsheet.xlsx', 'Meeting Notes']
                    window_title = f"{random.choice(docs)} - {app_name}"
                
                activity_data = {
                    'application_name': app_name,
                    'window_title': window_title,
                    'url': url,
                    'category': category,
                    'duration': duration,
                    'timestamp': timestamp
                }
                
                crud.create_activity_record(db, activity_data, user_id)
                activities.append(activity_data)
        
        print(f"Generated {len(activities)} sample activities for user {user_id}")
        return activities
        
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    # Create a test user if it doesn't exist
    db = SessionLocal()
    try:
        test_user = crud.get_user_by_username(db, "testuser")
        if not test_user:
            from schemas import UserCreate
            user_data = UserCreate(username="testuser", email="test@example.com", password="testpass123")
            test_user = crud.create_user(db, user_data)
            print(f"Created test user: {test_user.username}")
        
        # Generate sample data
        generate_sample_data(test_user.id, days=7)
        print("Sample data generation complete!")
        print(f"You can now login with username: testuser, password: testpass123")
        
    finally:
        db.close()

