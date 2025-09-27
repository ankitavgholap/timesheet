#!/usr/bin/env python3
"""
Comprehensive Database and Developer Check
Run this to see all developer data and sync status
"""

import os
import sys
from datetime import datetime, timedelta

print("=" * 60)
print("TIMESHEET DATABASE CHECK")
print("=" * 60)

# Check Python dependencies
try:
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    import json
    print("✅ Dependencies loaded successfully")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nTo install dependencies:")
    print("pip install sqlalchemy psycopg2-binary python-dotenv")
    sys.exit(1)

# Load environment
load_dotenv('.env')
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:asdf1234@localhost:5432/timesheet")
print(f"\n📌 Database URL: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    print("✅ Database engine created")
    
    with engine.connect() as conn:
        print("✅ Connected to database\n")
        
        # 1. DEVELOPER OVERVIEW
        print("👥 DEVELOPER OVERVIEW")
        print("-" * 40)
        
        developers = conn.execute(text("""
            SELECT 
                d.developer_id,
                d.name,
                d.api_token,
                d.created_at,
                COUNT(ar.id) as activity_count,
                MAX(ar.timestamp) as last_activity
            FROM developers d
            LEFT JOIN activity_records ar ON d.developer_id = ar.developer_id
            WHERE d.active = true
            GROUP BY d.developer_id, d.name, d.api_token, d.created_at
            ORDER BY d.created_at DESC
        """)).fetchall()
        
        if not developers:
            print("❌ No developers found!")
            print("\nTo register a developer:")
            print("1. Visit: http://api-timesheet.firsteconomy.com/register-developer")
            print("2. Enter developer name and API token")
            print("3. Start syncing with sync.sh\n")
        else:
            print(f"Found {len(developers)} developers:\n")
            
            for dev in developers:
                dev_id, name, token, created, activities, last_sync = dev
                token_short = f"{token[:20]}..." if token else "NO TOKEN"
                
                print(f"Developer: {name} ({dev_id})")
                print(f"  Token: {token_short}")
                print(f"  Created: {created}")
                print(f"  Activities: {activities}")
                
                if last_sync:
                    time_diff = datetime.now() - last_sync
                    if time_diff.total_seconds() < 3600:
                        sync_status = f"✅ Active ({int(time_diff.total_seconds() / 60)} min ago)"
                    elif time_diff.total_seconds() < 86400:
                        sync_status = f"⚠️  Inactive ({int(time_diff.total_seconds() / 3600)} hours ago)"
                    else:
                        sync_status = f"❌ Inactive ({last_sync.date()})"
                else:
                    sync_status = "❌ Never synced"
                
                print(f"  Sync Status: {sync_status}\n")
        
        # 2. TODAY'S ACTIVITY
        print("\n📊 TODAY'S ACTIVITY")
        print("-" * 40)
        
        today_data = conn.execute(text("""
            SELECT 
                developer_id,
                COUNT(*) as events,
                SUM(duration) / 3600.0 as hours,
                MIN(timestamp) as first_activity,
                MAX(timestamp) as last_activity
            FROM activity_records
            WHERE DATE(timestamp) = CURRENT_DATE
            GROUP BY developer_id
            ORDER BY hours DESC
        """)).fetchall()
        
        if today_data:
            total_hours_today = 0
            for dev_id, events, hours, first, last in today_data:
                total_hours_today += hours
                print(f"{dev_id}:")
                print(f"  Events: {events}")
                print(f"  Hours: {hours:.2f}")
                print(f"  Active: {first.strftime('%H:%M')} - {last.strftime('%H:%M')}\n")
            
            print(f"Total Hours Today: {total_hours_today:.2f}")
        else:
            print("No activity recorded today")
        
        # 3. RECENT SYNC ACTIVITY
        print("\n🔄 RECENT SYNC ACTIVITY (Last 10)")
        print("-" * 40)
        
        recent_syncs = conn.execute(text("""
            SELECT 
                developer_id,
                timestamp,
                duration,
                created_at
            FROM activity_records
            ORDER BY created_at DESC
            LIMIT 10
        """)).fetchall()
        
        if recent_syncs:
            for dev_id, timestamp, duration, created in recent_syncs:
                sync_delay = (created - timestamp).total_seconds() if timestamp and created else 0
                print(f"{timestamp} | {dev_id} | Duration: {duration}s | Sync delay: {sync_delay:.0f}s")
        else:
            print("No recent sync activity")
        
        # 4. SYNC ISSUES
        print("\n⚠️  POTENTIAL ISSUES")
        print("-" * 40)
        
        # Developers with no recent activity
        inactive_devs = conn.execute(text("""
            SELECT 
                d.developer_id,
                d.name,
                MAX(ar.timestamp) as last_activity
            FROM developers d
            LEFT JOIN activity_records ar ON d.developer_id = ar.developer_id
            WHERE d.active = true
            GROUP BY d.developer_id, d.name
            HAVING MAX(ar.timestamp) IS NULL 
                OR MAX(ar.timestamp) < NOW() - INTERVAL '24 hours'
        """)).fetchall()
        
        if inactive_devs:
            print("Inactive developers (no activity in 24h):")
            for dev_id, name, last in inactive_devs:
                if last:
                    print(f"  - {name} ({dev_id}) - Last: {last}")
                else:
                    print(f"  - {name} ({dev_id}) - Never synced")
        
        # Check for duplicate tokens
        dup_tokens = conn.execute(text("""
            SELECT api_token, COUNT(*) as count
            FROM developers
            WHERE api_token IS NOT NULL
            GROUP BY api_token
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if dup_tokens:
            print("\n❌ Duplicate API tokens found:")
            for token, count in dup_tokens:
                print(f"  - Token {token[:20]}... used by {count} developers")
        
        # 5. DATABASE STATS
        print("\n📈 DATABASE STATISTICS")
        print("-" * 40)
        
        stats = conn.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM developers) as total_devs,
                (SELECT COUNT(*) FROM developers WHERE active = true) as active_devs,
                (SELECT COUNT(*) FROM activity_records) as total_records,
                (SELECT pg_size_pretty(pg_total_relation_size('activity_records'))) as table_size,
                (SELECT MIN(timestamp) FROM activity_records) as oldest_record,
                (SELECT MAX(timestamp) FROM activity_records) as newest_record
        """)).fetchone()
        
        print(f"Total Developers: {stats[0]} ({stats[1]} active)")
        print(f"Total Records: {stats[2]}")
        print(f"Table Size: {stats[4]}")
        print(f"Data Range: {stats[4]} to {stats[5]}")
        
except Exception as e:
    print(f"\n❌ Database Error: {e}")
    print("\nPossible issues:")
    print("1. PostgreSQL not running")
    print("2. Database 'timesheet' doesn't exist")
    print("3. Wrong credentials in .env file")
    print("4. Tables not created")
    
    print("\nTo fix:")
    print("1. Start PostgreSQL: pg_ctl start -D 'C:\\Program Files\\PostgreSQL\\16\\data'")
    print("2. Create database: createdb -U postgres timesheet")
    print("3. Check .env file has correct DATABASE_URL")
    print("4. Run migrations: python run_backend.py (this creates tables)")

print("\n" + "=" * 60)
print("END OF DATABASE CHECK")
print("=" * 60)
