#!/usr/bin/env python3
"""
Test the productivity calculation with current data
"""
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from database import SessionLocal
from productivity_calculator import ProductivityCalculator

load_dotenv()

def test_productivity():
    """Test productivity calculation with current data"""
    db = SessionLocal()
    
    try:
        print("🧠 Testing Productivity Calculation")
        print("=" * 50)
        
        # Test with today's data
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        calculator = ProductivityCalculator()
        
        # Use the admin user (user_id = 2) which has the activity data
        user_id = 2
        
        analysis = calculator.calculate_productivity_score(db, user_id, today, tomorrow)
        
        print(f"📊 Productivity Analysis for {today.date()}")
        print("-" * 40)
        print(f"Overall Score: {analysis['overall_score']}/100")
        print(f"Total Time: {analysis['total_time']/3600:.2f} hours")
        print(f"Productive Time: {analysis['productive_time']/3600:.2f} hours")
        print(f"Productivity Percentage: {analysis['productivity_percentage']:.1f}%")
        print(f"Focus Sessions: {analysis['focus_sessions']}")
        
        if analysis['longest_focus_session'] > 0:
            print(f"Longest Focus Session: {analysis['longest_focus_session']/60:.1f} minutes")
        
        print()
        print("📈 Category Breakdown:")
        print("-" * 30)
        for category, data in analysis['category_breakdown'].items():
            hours = data['time_spent'] / 3600
            print(f"{category:15} | {hours:5.2f}h | {data['productivity_rate']:5.1f}% productive")
        
        print()
        print("💡 Recommendations:")
        print("-" * 20)
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"{i}. {rec}")
        
        print()
        print(f"📈 Productivity Trend: {analysis['productivity_trend']['trend'].title()}")
        if analysis['productivity_trend']['change'] != 0:
            change = analysis['productivity_trend']['change']
            print(f"   Change: {'+' if change > 0 else ''}{change:.1f}%")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_productivity()
