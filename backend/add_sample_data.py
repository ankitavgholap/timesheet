#!/usr/bin/env python3
"""
Quick test to add sample activity data to see your dashboard working
"""

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import random

# Load environment
load_dotenv('.env.local')
DATABASE_URL = os.getenv("DATABASE_URL")

print("📊 Adding sample activity data for testing...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if we have any developers
        dev_check = conn.execute(text("SELECT developer_id FROM developers WHERE active = true LIMIT 1"))
        developer = dev_check.fetchone()
        
        if not developer:
            print("❌ No active developers found. Please register a developer first.")
            print("Visit: http://localhost:8000/register-developer")
            exit(1)
        
        developer_id = developer[0]
        print(f"✅ Found developer: {developer_id}")
        
        # Generate sample activities for the last few hours
        now = datetime.now(timezone.utc)
        sample_activities = [
            {
                'app': 'Cursor.exe',
                'title': 'package.json - timesheet_new - Cursor',
                'duration': 1800,  # 30 minutes
                'category': 'development'
            },
            {
                'app': 'chrome.exe', 
                'title': 'React Documentation - Chrome',
                'duration': 900,   # 15 minutes
                'category': 'browser'
            },
            {
                'app': 'Cursor.exe',
                'title': 'main.py - timesheet_new - Cursor',
                'duration': 2400,  # 40 minutes
                'category': 'development'
            },
            {
                'app': 'chrome.exe',
                'title': 'localhost:3000 - React App - Chrome',
                'duration': 600,   # 10 minutes
                'category': 'browser'
            },
            {
                'app': 'FileZilla.exe',
                'title': 'FileZilla - server.example.com',
                'duration': 300,   # 5 minutes
                'category': 'general'
            },
            {
                'app': 'DataGrip.exe',
                'title': 'timesheet@localhost - DataGrip',
                'duration': 720,   # 12 minutes
                'category': 'general'
            }
        ]
        
        # Insert sample activities
        insert_query = text("""
            INSERT INTO activity_records (
                developer_id, developer_name, application_name, window_title,
                category, duration, timestamp, created_at
            ) VALUES (
                :developer_id, :developer_name, :application_name, :window_title,
                :category, :duration, :timestamp, :created_at
            )
        """)
        
        activities_added = 0
        
        for i, activity in enumerate(sample_activities):
            # Space activities over the last 4 hours
            timestamp = now - timedelta(hours=4) + timedelta(minutes=i * 30)
            
            conn.execute(insert_query, {
                'developer_id': developer_id,
                'developer_name': developer_id,
                'application_name': activity['app'],
                'window_title': activity['title'],
                'category': activity['category'],
                'duration': activity['duration'],
                'timestamp': timestamp,
                'created_at': now
            })
            activities_added += 1
        
        conn.commit()
        
        print(f"✅ Added {activities_added} sample activities")
        print(f"📊 Total duration: {sum(a['duration'] for a in sample_activities) / 3600:.1f} hours")
        print("\n🎯 Now your dashboard should show:")
        print("   - Project Details with window titles")
        print("   - Activity charts with data")
        print("   - Productivity analysis")
        print("\n🚀 Visit your dashboard to see the data!")
        
except Exception as e:
    print(f"❌ Error: {e}")
