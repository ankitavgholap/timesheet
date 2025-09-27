#!/usr/bin/env python3
"""
Check developer data in the database
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import json

# Load environment
load_dotenv('.env')
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:asdf1234@localhost:5432/timesheet")

print("🔍 Checking Developer Data...")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # 1. Check developers table
        print("\n📋 DEVELOPERS TABLE:")
        print("-" * 40)
        
        # Get all developers
        result = conn.execute(text("""
            SELECT 
                id,
                developer_id,
                name,
                email,
                api_token,
                active,
                created_at,
                last_sync
            FROM developers
            ORDER BY created_at DESC
        """))
        
        developers = result.fetchall()
        print(f"Total Developers: {len(developers)}")
        
        for dev in developers:
            print(f"\nDeveloper #{dev[0]}:")
            print(f"  ID: {dev[1]}")
            print(f"  Name: {dev[2]}")
            print(f"  Email: {dev[3]}")
            print(f"  Token: {dev[4][:20]}..." if dev[4] else "No token")
            print(f"  Active: {dev[5]}")
            print(f"  Created: {dev[6]}")
            print(f"  Last Sync: {dev[7]}")
        
        # 2. Check activity_records table
        print("\n\n📊 ACTIVITY RECORDS:")
        print("-" * 40)
        
        # Get activity summary by developer
        result = conn.execute(text("""
            SELECT 
                developer_id,
                COUNT(*) as record_count,
                MIN(timestamp) as first_activity,
                MAX(timestamp) as last_activity,
                SUM(duration) / 3600.0 as total_hours
            FROM activity_records
            WHERE developer_id IS NOT NULL
            GROUP BY developer_id
            ORDER BY last_activity DESC
        """))
        
        activities = result.fetchall()
        print(f"Developers with Activities: {len(activities)}")
        
        for act in activities:
            print(f"\nDeveloper: {act[0]}")
            print(f"  Records: {act[1]}")
            print(f"  First Activity: {act[2]}")
            print(f"  Last Activity: {act[3]}")
            print(f"  Total Hours: {act[4]:.2f}")
        
        # 3. Recent activity (last 24 hours)
        print("\n\n⏰ RECENT ACTIVITY (Last 24 hours):")
        print("-" * 40)
        
        yesterday = datetime.now() - timedelta(days=1)
        result = conn.execute(text("""
            SELECT 
                developer_id,
                COUNT(*) as activities,
                SUM(duration) / 3600.0 as hours
            FROM activity_records
            WHERE timestamp > :yesterday
            GROUP BY developer_id
            ORDER BY hours DESC
        """), {"yesterday": yesterday})
        
        recent = result.fetchall()
        if recent:
            for r in recent:
                print(f"{r[0]}: {r[1]} activities, {r[2]:.2f} hours")
        else:
            print("No activity in the last 24 hours")
        
        # 4. Check for sync issues
        print("\n\n🔧 SYNC STATUS:")
        print("-" * 40)
        
        # Developers with no activity
        result = conn.execute(text("""
            SELECT d.developer_id, d.name, d.created_at
            FROM developers d
            LEFT JOIN activity_records ar ON d.developer_id = ar.developer_id
            WHERE ar.id IS NULL
            AND d.active = true
        """))
        
        no_activity = result.fetchall()
        if no_activity:
            print("Developers with NO activity data:")
            for dev in no_activity:
                print(f"  - {dev[1]} ({dev[0]}) - Registered: {dev[2]}")
        else:
            print("✅ All active developers have activity data")
        
        # 5. Sample activity data
        print("\n\n📝 SAMPLE ACTIVITY DATA (Last 5 records):")
        print("-" * 40)
        
        result = conn.execute(text("""
            SELECT 
                developer_id,
                timestamp,
                duration,
                activity_data
            FROM activity_records
            ORDER BY timestamp DESC
            LIMIT 5
        """))
        
        samples = result.fetchall()
        for i, sample in enumerate(samples):
            print(f"\nRecord {i+1}:")
            print(f"  Developer: {sample[0]}")
            print(f"  Time: {sample[1]}")
            print(f"  Duration: {sample[2]} seconds")
            if sample[3]:
                try:
                    data = json.loads(sample[3]) if isinstance(sample[3], str) else sample[3]
                    print(f"  Data: {json.dumps(data, indent=4)[:200]}...")
                except:
                    print(f"  Data: {str(sample[3])[:200]}...")
        
        # 6. Check table structure
        print("\n\n🏗️ TABLE STRUCTURE:")
        print("-" * 40)
        
        # Check developers table columns
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'developers'
            ORDER BY ordinal_position
        """))
        
        print("DEVELOPERS table columns:")
        for col in result:
            print(f"  - {col[0]} ({col[1]}) {'' if col[2] == 'YES' else 'NOT NULL'}")
        
        # Check activity_records table columns  
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'activity_records'
            ORDER BY ordinal_position
        """))
        
        print("\nACTIVITY_RECORDS table columns:")
        for col in result:
            print(f"  - {col[0]} ({col[1]}) {'' if col[2] == 'YES' else 'NOT NULL'}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Database URL: {DATABASE_URL}")
