#!/usr/bin/env python3
"""
Test ActivityWatch-based daily breakdown calculation
"""
from realistic_hours_calculator import RealisticHoursCalculator
from datetime import datetime, timezone, timedelta

def test_activitywatch_daily():
    """Test the new ActivityWatch-based daily calculation"""
    calculator = RealisticHoursCalculator()
    
    # Test with current date range
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)  # Last 7 days
    
    print("🔍 TESTING ACTIVITYWATCH-BASED DAILY BREAKDOWN")
    print(f"📅 Date range: {start.date()} to {end.date()}")
    print("=" * 60)
    
    try:
        # Get daily data from ActivityWatch
        daily_data = calculator.calculate_daily_hours_from_activitywatch(start, end)
        
        print(f"📊 Found data for {len(daily_data)} days")
        print("\n📋 DAILY BREAKDOWN:")
        print("-" * 80)
        
        for day in daily_data:
            if day['activities_count'] > 0:
                print(f"{day['date']}: {day['working_hours_formatted']} work / {day['total_hours_formatted']} total")
                print(f"   {day['activities_count']} activities • {day['productivity_percentage']}% productive • {day['status_message']}")
            else:
                print(f"{day['date']}: No activity")
        
        # Show summary
        total_work_hours = sum(day['working_hours'] for day in daily_data)
        total_hours = sum(day['total_hours'] for day in daily_data)
        active_days = len([day for day in daily_data if day['activities_count'] > 0])
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total work time: {calculator.format_time_readable(total_work_hours)}")
        print(f"   Total computer time: {calculator.format_time_readable(total_hours)}")
        print(f"   Active days: {active_days}/{len(daily_data)}")
        print(f"   Overall productivity: {(total_work_hours/total_hours*100):.1f}%" if total_hours > 0 else "   Overall productivity: 0%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_activitywatch_daily()
