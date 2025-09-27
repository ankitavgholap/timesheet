#!/usr/bin/env python3
"""
Quick database check for developer and activity data
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment
load_dotenv('.env')
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:asdf1234@localhost:5432/timesheet")

print("🚀 Quick Database Check")
print("=" * 50)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # 1. Developer Summary
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_developers,
                COUNT(CASE WHEN active = true THEN 1 END) as active_developers,
                COUNT(CASE WHEN api_token IS NOT NULL THEN 1 END) as with_tokens
            FROM developers
        """))
        
        dev_stats = result.fetchone()
        print(f"\n👥 DEVELOPERS:")
        print(f"   Total: {dev_stats[0]}")
        print(f"   Active: {dev_stats[1]}")
        print(f"   With Tokens: {dev_stats[2]}")
        
        # 2. Activity Summary
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT developer_id) as developers_with_data,
                MIN(timestamp) as oldest_activity,
                MAX(timestamp) as newest_activity
            FROM activity_records
            WHERE developer_id IS NOT NULL
        """))
        
        act_stats = result.fetchone()
        print(f"\n📊 ACTIVITIES:")
        print(f"   Total Records: {act_stats[0]}")
        print(f"   Developers with Data: {act_stats[1]}")
        print(f"   Date Range: {act_stats[2]} to {act_stats[3]}")
        
        # 3. Today's Activity
        result = conn.execute(text("""
            SELECT 
                developer_id,
                COUNT(*) as activities_today,
                SUM(duration) / 3600.0 as hours_today
            FROM activity_records
            WHERE DATE(timestamp) = CURRENT_DATE
            GROUP BY developer_id
            ORDER BY hours_today DESC
        """))
        
        today_data = result.fetchall()
        print(f"\n📅 TODAY'S ACTIVITY:")
        if today_data:
            for dev in today_data:
                print(f"   {dev[0]}: {dev[1]} activities, {dev[2]:.2f} hours")
        else:
            print("   No activity recorded today")
        
        # 4. Developer List
        result = conn.execute(text("""
            SELECT 
                developer_id,
                name,
                api_token,
                created_at
            FROM developers
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        developers = result.fetchall()
        print(f"\n📋 DEVELOPER LIST (Recent 10):")
        for dev in developers:
            token_display = f"{dev[2][:20]}..." if dev[2] else "No token"
            print(f"   - {dev[1]} (ID: {dev[0]}) - Token: {token_display} - Created: {dev[3]}")
            
        # 5. Check for Issues
        print(f"\n⚠️  POTENTIAL ISSUES:")
        
        # Developers without activity
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM developers d
            LEFT JOIN activity_records ar ON d.developer_id = ar.developer_id
            WHERE ar.id IS NULL AND d.active = true
        """))
        
        no_activity_count = result.scalar()
        if no_activity_count > 0:
            print(f"   - {no_activity_count} active developers have NO activity data")
        
        # Check for test data
        result = conn.execute(text("""
            SELECT COUNT(DISTINCT developer_id)
            FROM activity_records
            WHERE developer_id IN ('test', 'demo', 'example', 'john_doe', 'jane_doe')
        """))
        
        test_data = result.scalar()
        if test_data > 0:
            print(f"   - Found {test_data} test/demo developers with data")
            
        # Missing columns check
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'developers'
            AND column_name IN ('ip_address', 'activitywatch_port', 'last_sync')
        """))
        
        column_count = result.scalar()
        if column_count < 3:
            print(f"   - Missing some tracking columns (found {column_count}/3)")
            
except Exception as e:
    print(f"\n❌ Database Connection Error:")
    print(f"   {e}")
    print(f"\nPlease check:")
    print(f"1. PostgreSQL is running")
    print(f"2. Database 'timesheet' exists")
    print(f"3. .env file has correct DATABASE_URL")
    print(f"\nCurrent DATABASE_URL: {DATABASE_URL}")
