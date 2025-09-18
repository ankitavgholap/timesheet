#!/usr/bin/env python3
"""
Explain how productivity calculation works with examples
"""

def explain_productivity_calculation():
    print("🧠 HOW PRODUCTIVITY IS CALCULATED")
    print("=" * 60)
    
    print("\n1️⃣ CATEGORY-BASED SCORING")
    print("-" * 30)
    print("Each activity gets a base productivity score based on its category:")
    print("• Development (IDE work):     100% productive")
    print("• Database work:              95% productive") 
    print("• Productivity tools:         95% productive")
    print("• Browser (general):          20% productive")
    print("• Entertainment:              0% productive")
    print("• System/Other:               10-15% productive")
    
    print("\n📝 EXAMPLE:")
    print("- 2 hours coding in Cursor:   2h × 100% = 2.0 productive hours")
    print("- 1 hour on YouTube:          1h × 20%  = 0.2 productive hours")
    print("- 30min database work:        0.5h × 95% = 0.475 productive hours")
    
    print("\n2️⃣ TIME-OF-DAY MULTIPLIERS")
    print("-" * 30)
    print("Activities get multiplied based on when you do them:")
    print("• Peak hours (9 AM - 5 PM):   1.2x multiplier")
    print("• Evening (5 PM - 9 PM):      0.9x multiplier")
    print("• Night (9 PM - 11 PM):       0.7x multiplier")
    print("• Late night (11 PM - 6 AM):  0.5x multiplier")
    
    print("\n📝 EXAMPLE:")
    print("- Coding at 10 AM:    1.0 × 1.2 = 1.2 effective productivity")
    print("- YouTube at 11 PM:   0.2 × 0.7 = 0.14 effective productivity")
    
    print("\n3️⃣ FOCUS SESSION BONUSES")
    print("-" * 30)
    print("Continuous work on the same productive category gets bonuses:")
    print("• 30-60 minutes:      1.1x bonus")
    print("• 1-2 hours:          1.2x bonus")
    print("• 2-3 hours:          1.3x bonus")
    print("• 3+ hours:           1.5x bonus (deep focus)")
    
    print("\n📝 EXAMPLE:")
    print("- 2.5 hour coding session: Gets 1.3x focus bonus")
    print("- Switching every 10 minutes: No focus bonus")
    
    print("\n4️⃣ FINAL CALCULATION")
    print("-" * 30)
    print("Formula for each activity:")
    print("Productive Time = Duration × Category Weight × Time Multiplier × Focus Bonus")
    print()
    print("Overall Score = (Total Productive Time / Total Time) × 100")
    
    print("\n📊 COMPLETE EXAMPLE")
    print("-" * 30)
    print("Your day:")
    print("• 9 AM - 11 AM: Coding (2h)")
    print("• 11 AM - 12 PM: YouTube (1h)")
    print("• 2 PM - 4 PM: Database work (2h)")
    print("• 8 PM - 9 PM: Email (1h)")
    print()
    print("Calculations:")
    print("• Coding:    2h × 1.0 × 1.2 × 1.2 = 2.88 productive hours")
    print("• YouTube:   1h × 0.2 × 1.2 × 1.0 = 0.24 productive hours")
    print("• Database:  2h × 0.95 × 1.2 × 1.2 = 2.74 productive hours")
    print("• Email:     1h × 0.2 × 0.9 × 1.0 = 0.18 productive hours")
    print()
    print("Total: 6.04 productive hours out of 6 total hours")
    print("Productivity Score: (6.04 / 6) × 100 = 100.7% → Capped at 100%")
    
    print("\n5️⃣ SMART FEATURES")
    print("-" * 30)
    print("• Website Detection: Recognizes work vs entertainment sites")
    print("• File Path Analysis: Coding on work projects vs personal")
    print("• Trend Analysis: Compares first half vs second half of day")
    print("• Personalized Recommendations: Based on your patterns")
    
    print("\n6️⃣ WHAT AFFECTS YOUR SCORE")
    print("-" * 30)
    print("✅ INCREASES SCORE:")
    print("• More time in IDE/database tools")
    print("• Longer focus sessions")
    print("• Working during peak hours")
    print("• Work-related browsing")
    print()
    print("❌ DECREASES SCORE:")
    print("• YouTube, social media, entertainment")
    print("• Frequent task switching")
    print("• Late night non-productive activities")
    print("• Long breaks or idle time")

if __name__ == "__main__":
    explain_productivity_calculation()








