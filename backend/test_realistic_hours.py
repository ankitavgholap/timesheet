#!/usr/bin/env python3
"""
Test the realistic hours calculation
"""
from datetime import datetime, timezone, timedelta
from database import SessionLocal
from realistic_hours_calculator import RealisticHoursCalculator

def test_realistic_hours():
    """Test realistic hours calculation with current data"""
    db = SessionLocal()
    
    try:
        print("📅 Testing Realistic Hours Calculation")
        print("=" * 60)
        
        # Test with September 1-14
        start_date = datetime(2025, 9, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 9, 14, tzinfo=timezone.utc)
        
        calculator = RealisticHoursCalculator()
        
        # Use admin user (user_id = 2) which has the activity data
        user_id = 2
        
        report = calculator.calculate_daily_report(db, user_id, start_date, end_date)
        
        print(f"📊 Realistic Hours Report ({report['date_range']['start']} to {report['date_range']['end']})")
        print("-" * 70)
        
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
        print("-" * 50)
        
        for day in report['daily_data']:
            if day['working_hours'] > 0:  # Only show days with activity
                status_icon = {
                    'high': '🟢',
                    'medium': '🟡', 
                    'low': '🔴'
                }.get(day['status'], '⚪')
                
                print(f"{status_icon} {day['date']}: {day['working_hours']}h working ({day['total_hours']}h total)")
                print(f"   Activities: {day['activities_count']} | Productivity: {day['productivity_percentage']}%")
                
                # Show breakdown
                if day['breakdown']:
                    print("   Breakdown:")
                    for category, data in day['breakdown'].items():
                        print(f"     • {category}: {data['working_hours']:.2f}h/{data['total_hours']:.2f}h ({data['percentage']}%)")
                print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_realistic_hours()
