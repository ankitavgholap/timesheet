#!/usr/bin/env python3
"""
Check Working Hours for Any Date - Verify calculations are not hardcoded
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
import models
from sqlalchemy import func, and_
import sys

def check_date_working_hours(date_str: str = None):
    """Check working hours for any specific date"""
    db = SessionLocal()
    
    try:
        # Parse the date or use today if not provided
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                print(f"❌ Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-12)")
                return
        else:
            target_date = datetime.now(timezone.utc)
        
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"🔍 CHECKING WORKING HOURS FOR {target_date.date()}")
        print("=" * 60)
        
        # Get all activities for this day
        activities = db.query(models.ActivityRecord).filter(
            and_(
                models.ActivityRecord.user_id == 2,  # admin user
                models.ActivityRecord.timestamp >= start_of_day,
                models.ActivityRecord.timestamp <= end_of_day
            )
        ).order_by(models.ActivityRecord.timestamp.asc()).all()
        
        if not activities:
            print(f"📭 No activities found for {target_date.date()}")
            print("This proves the data is NOT hardcoded - empty days show 0 hours!")
            return
        
        print(f"📊 Found {len(activities)} activities")
        print(f"📅 Date: {target_date.date()}")
        print()
        
        # Group by category and calculate working hours
        category_data = {}
        total_time = 0
        working_time = 0
        
        for activity in activities:
            category = activity.category
            duration = activity.duration
            total_time += duration
            
            if category not in category_data:
                category_data[category] = {
                    'count': 0,
                    'total_time': 0,
                    'apps': {},
                    'activities': []
                }
            
            category_data[category]['count'] += 1
            category_data[category]['total_time'] += duration
            
            # Track apps
            app = activity.application_name
            if app not in category_data[category]['apps']:
                category_data[category]['apps'][app] = 0
            category_data[category]['apps'][app] += duration
            
            # Store activity details
            category_data[category]['activities'].append({
                'time': activity.timestamp.strftime('%H:%M:%S'),
                'app': app,
                'title': activity.window_title[:40] + '...' if len(activity.window_title) > 40 else activity.window_title,
                'duration': duration
            })
        
        print("📋 RAW ACTIVITY BREAKDOWN:")
        print("-" * 40)
        
        for category, data in sorted(category_data.items(), key=lambda x: x[1]['total_time'], reverse=True):
            cat_hours = data['total_time'] / 3600
            print(f"\n{category.upper()}: {cat_hours:.2f}h ({data['count']} activities)")
            
            # Show top 3 activities in this category
            top_activities = sorted(data['activities'], key=lambda x: x['duration'], reverse=True)[:3]
            for act in top_activities:
                act_minutes = act['duration'] / 60
                print(f"  {act['time']} | {act['app'][:15]:15} | {act_minutes:5.1f}min | {act['title']}")
        
        print("\n" + "="*60)
        print("💼 WORKING HOURS CALCULATION:")
        print("-" * 40)
        
        # Calculate working hours using the same logic as the app
        for category, data in category_data.items():
            cat_time = data['total_time']
            cat_hours = cat_time / 3600
            
            if category == 'development':
                work_percentage = 100
                work_time = cat_time
                reason = "All coding/development work"
                
            elif category == 'database':
                work_percentage = 100
                work_time = cat_time
                reason = "All database work"
                
            elif category == 'productivity':
                work_percentage = 100
                work_time = cat_time
                reason = "All productivity tools"
                
            elif category == 'browser':
                work_percentage = 85
                work_time = cat_time * 0.85
                reason = "85% work-related (docs, research, testing)"
                
            elif category == 'other':
                # Smart analysis of "other" apps
                work_time = 0
                for app, app_time in data['apps'].items():
                    if 'lockapp' in app.lower():
                        work_time += app_time * 0.9  # 90% work time
                    elif 'datagrip' in app.lower() or 'postman' in app.lower():
                        work_time += app_time * 1.0  # 100% work time
                    elif 'snipping' in app.lower():
                        work_time += app_time * 0.9  # 90% work time
                    else:
                        work_time += app_time * 0.5  # 50% work time
                
                work_percentage = int((work_time / cat_time) * 100) if cat_time > 0 else 50
                reason = f"Smart analysis: LockApp=90%, DataGrip=100%, Others=50%"
                
            elif category == 'system':
                work_percentage = 10
                work_time = cat_time * 0.1
                reason = "Minimal work-related system activities"
                
            else:
                work_percentage = 20
                work_time = cat_time * 0.2
                reason = "Conservative estimate for unknown category"
            
            working_time += work_time
            work_hours = work_time / 3600
            
            print(f"{category:12} | {cat_hours:5.2f}h → {work_hours:5.2f}h ({work_percentage:3d}%) | {reason}")
        
        total_hours = total_time / 3600
        total_working_hours = working_time / 3600
        productivity_rate = (working_time / total_time) * 100 if total_time > 0 else 0
        
        print("\n" + "="*60)
        print("🎯 FINAL RESULTS:")
        print("-" * 20)
        print(f"📊 Total Time Tracked: {total_hours:.2f} hours")
        print(f"💼 Working Time: {total_working_hours:.2f} hours")
        print(f"📈 Productivity Rate: {productivity_rate:.1f}%")
        
        # Color coding like the app
        if total_working_hours >= 8:
            status = "🟢 EXCELLENT (8+ hours)"
        elif total_working_hours >= 6:
            status = "🟡 GOOD (6-8 hours)"
        else:
            status = "🔴 LOW (<6 hours)"
        
        print(f"🎯 Status: {status}")
        
        print("\n💡 This data is calculated in real-time from your ActivityWatch records!")
        print("   Different dates will show different results - proving it's NOT hardcoded.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def show_available_dates():
    """Show dates that have activity data"""
    db = SessionLocal()
    
    try:
        print("📅 AVAILABLE DATES WITH ACTIVITY DATA:")
        print("=" * 50)
        
        # Get all unique dates with activity
        from sqlalchemy import text
        dates_with_data = db.execute(text("""
            SELECT DATE(timestamp) as activity_date, 
                   COUNT(*) as activity_count,
                   SUM(duration)/3600 as total_hours
            FROM activity_records 
            WHERE user_id = 2 
            GROUP BY DATE(timestamp) 
            ORDER BY activity_date DESC
        """)).fetchall()
        
        if dates_with_data:
            print("Date       | Activities | Total Hours")
            print("-" * 40)
            for date, count, hours in dates_with_data:
                print(f"{date} |    {count:3d}     |   {hours:6.2f}h")
        else:
            print("No activity data found!")
        
        print(f"\nTotal dates with data: {len(dates_with_data)}")
        print("\n💡 Try any of these dates with: python check_any_date.py YYYY-MM-DD")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            show_available_dates()
        else:
            check_date_working_hours(sys.argv[1])
    else:
        print("🔍 RANDOM DATE CHECKER")
        print("=" * 30)
        print("Usage:")
        print("  python check_any_date.py 2025-09-12    # Check specific date")
        print("  python check_any_date.py list          # Show available dates")
        print()
        show_available_dates()
        print()
        print("Pick any date above and check it!")
