#!/usr/bin/env python3
"""
Explain Dashboard Numbers - What Total Time and Avg Hours mean
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
import models
from sqlalchemy import func, and_

def explain_dashboard_numbers():
    """Explain what the dashboard numbers represent"""
    db = SessionLocal()
    
    try:
        print("📊 DASHBOARD NUMBERS EXPLAINED")
        print("=" * 50)
        
        # Get all activity data for admin user
        user_id = 2
        activities = db.query(models.ActivityRecord).filter(
            models.ActivityRecord.user_id == user_id
        ).all()
        
        if not activities:
            print("No activities found!")
            return
        
        # Calculate total time
        total_seconds = sum(activity.duration for activity in activities)
        total_hours = total_seconds / 3600
        total_minutes = (total_seconds % 3600) / 60
        
        print(f"🕐 TOTAL TIME: {int(total_hours)}h {int(total_minutes)}m {int(total_seconds % 60)}s")
        print(f"   = {total_hours:.2f} hours")
        print(f"   = ALL activity time tracked by ActivityWatch")
        print(f"   = Every second you spent on any application")
        print()
        
        # Get unique dates with activity
        dates_with_activity = set()
        for activity in activities:
            dates_with_activity.add(activity.timestamp.date())
        
        working_days = len(dates_with_activity)
        avg_hours = total_hours / working_days if working_days > 0 else 0
        
        print(f"📅 WORKING DAYS: {working_days}")
        print(f"   = Days with ANY activity recorded")
        print(f"   = Not calendar days, only days you used your computer")
        print()
        
        print(f"📈 AVG HOURS: {avg_hours:.2f}h")
        print(f"   = Total Time ÷ Working Days")
        print(f"   = {total_hours:.2f}h ÷ {working_days} days = {avg_hours:.2f}h per day")
        print(f"   = Average computer usage per active day")
        print()
        
        print("🔍 BREAKDOWN BY DATE:")
        print("-" * 30)
        
        # Show daily breakdown
        daily_data = {}
        for activity in activities:
            date = activity.timestamp.date()
            if date not in daily_data:
                daily_data[date] = 0
            daily_data[date] += activity.duration
        
        for date in sorted(daily_data.keys(), reverse=True):
            hours = daily_data[date] / 3600
            print(f"{date}: {hours:.2f}h")
        
        print()
        print("💡 KEY DIFFERENCES:")
        print("-" * 25)
        print("📊 TOTAL TIME:")
        print("   • Raw computer usage time")
        print("   • Includes ALL activities (work + non-work)")
        print("   • From ActivityWatch tracking")
        print()
        print("💼 WORKING HOURS (from Daily Working Hours section):")
        print("   • Calculated productive time only")
        print("   • Development = 100%, Browser = 85%, etc.")
        print("   • Smart filtering of work vs non-work")
        print()
        print("📈 AVG HOURS:")
        print("   • Simple average: Total ÷ Days")
        print("   • Shows overall computer usage pattern")
        print("   • NOT the same as average working hours")
        
        # Show the difference
        print()
        print("🎯 EXAMPLE FROM YOUR DATA:")
        print("-" * 35)
        print(f"Total Computer Time: {total_hours:.2f}h")
        print(f"Estimated Working Time: ~{total_hours * 0.7:.2f}h (70% of total)")
        print(f"Average Computer Usage: {avg_hours:.2f}h per day")
        print(f"Average Working Time: ~{avg_hours * 0.7:.2f}h per day")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    explain_dashboard_numbers()








