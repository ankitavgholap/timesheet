#!/usr/bin/env python3
"""
Test the daily hours calculation
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from daily_hours_calculator import DailyHoursCalculator

def test_daily_hours():
    """Test daily hours calculation with current data"""
    db = SessionLocal()
    
    try:
        print("📅 Testing Daily Hours Calculation")
        print("=" * 50)
        
        # Test with last 7 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        calculator = DailyHoursCalculator()
        
        # Use admin user (user_id = 2) which has the activity data
        user_id = 2
        
        report = calculator.calculate_daily_report(db, user_id, start_date, end_date)
        
        print(f"📊 Daily Hours Report ({report['date_range']['start']} to {report['date_range']['end']})")
        print("-" * 60)
        
        # Summary
        summary = report['summary']
        print("📈 SUMMARY:")
        print(f"  Total Days: {summary['total_days']}")
        print(f"  Working Days: {summary['working_days']}")
        print(f"  Average Working Hours: {summary['avg_working_hours']}h")
        print(f"  Total Working Hours: {summary['total_working_hours']}h")
        print()
        print(f"  🟢 Days Above Target (8h+): {summary['days_above_target']}")
        print(f"  🟡 Days On Track (6-8h): {summary['days_on_track']}")
        print(f"  🔴 Days Below Target (<6h): {summary['days_below_target']}")
        
        if summary['best_day']:
            print(f"  🏆 Best Day: {summary['best_day']['date']} ({summary['best_day']['hours']}h)")
        
        print()
        print("📅 DAILY BREAKDOWN:")
        print("-" * 40)
        
        for day in report['daily_data']:
            status_icon = {
                'high': '🟢',
                'medium': '🟡', 
                'low': '🔴'
            }.get(day['status'], '⚪')
            
            print(f"{status_icon} {day['date']}: {day['working_hours']}h working ({day['total_hours']}h total)")
            print(f"   Status: {day['status_message']} | Activities: {day['activities_count']} | Productivity: {day['productivity_percentage']}%")
            
            if day['categories']:
                print("   Categories:", end=" ")
                for cat, data in day['categories'].items():
                    cat_hours = data['working_time'] / 3600
                    print(f"{cat}({cat_hours:.1f}h)", end=" ")
                print()
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_daily_hours()
