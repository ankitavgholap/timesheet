#!/usr/bin/env python3
"""
Debug working hours calculation to see what's wrong
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
import models
from sqlalchemy import func, and_

def debug_working_hours():
    """Debug the working hours calculation"""
    db = SessionLocal()
    
    try:
        print("🔍 Debugging Working Hours Calculation")
        print("=" * 60)
        
        # Check September 13th data (the day with most activity)
        target_date = datetime(2025, 9, 13, tzinfo=timezone.utc)
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"📅 Analyzing {target_date.date()}")
        print("-" * 40)
        
        # Get all activities for this day
        activities = db.query(models.ActivityRecord).filter(
            and_(
                models.ActivityRecord.user_id == 2,  # admin user
                models.ActivityRecord.timestamp >= start_of_day,
                models.ActivityRecord.timestamp <= end_of_day
            )
        ).order_by(models.ActivityRecord.timestamp.asc()).all()
        
        print(f"Total activities: {len(activities)}")
        
        # Group by category
        category_data = {}
        total_time = 0
        
        for activity in activities:
            category = activity.category
            duration = activity.duration
            total_time += duration
            
            if category not in category_data:
                category_data[category] = {
                    'count': 0,
                    'total_time': 0,
                    'activities': []
                }
            
            category_data[category]['count'] += 1
            category_data[category]['total_time'] += duration
            category_data[category]['activities'].append({
                'app': activity.application_name,
                'title': activity.window_title[:50] + '...' if len(activity.window_title) > 50 else activity.window_title,
                'duration': duration
            })
        
        print(f"Total time: {total_time/3600:.2f} hours")
        print()
        
        print("📊 Category Breakdown:")
        print("-" * 50)
        
        for category, data in sorted(category_data.items(), key=lambda x: x[1]['total_time'], reverse=True):
            hours = data['total_time'] / 3600
            print(f"{category.upper()}: {hours:.2f}h ({data['count']} activities)")
            
            # Show top activities in this category
            top_activities = sorted(data['activities'], key=lambda x: x['duration'], reverse=True)[:3]
            for act in top_activities:
                act_hours = act['duration'] / 3600
                print(f"  • {act['app']}: {act_hours:.2f}h - {act['title']}")
            print()
        
        # Calculate what should be "working hours"
        print("🎯 What Should Count as Working Hours:")
        print("-" * 40)
        
        productive_categories = ['development', 'database', 'productivity']
        working_time = 0
        
        for category in productive_categories:
            if category in category_data:
                cat_time = category_data[category]['total_time']
                working_time += cat_time
                hours = cat_time / 3600
                print(f"✅ {category}: {hours:.2f}h (100% productive)")
        
        # Partial working time (some browser usage might be work-related)
        if 'browser' in category_data:
            browser_time = category_data['browser']['total_time']
            # Let's assume 50% of browser time is work-related (not 30%)
            work_browser_time = browser_time * 0.5
            working_time += work_browser_time
            hours = browser_time / 3600
            work_hours = work_browser_time / 3600
            print(f"⚠️ browser: {hours:.2f}h total, {work_hours:.2f}h work-related (50%)")
        
        total_working_hours = working_time / 3600
        print(f"\n🎯 CORRECTED WORKING HOURS: {total_working_hours:.2f}h")
        print(f"📊 Productivity Rate: {(working_time/total_time*100):.1f}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_working_hours()
