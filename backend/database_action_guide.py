#!/usr/bin/env python3
"""
Database Action Guide - What to do based on your data
"""

print("""
📊 TIMESHEET DATABASE ACTION GUIDE
==================================

Based on your database check results, here's what to do:

🔴 IF YOU HAVE NO DEVELOPERS:
-----------------------------
1. Register developers first:
   - Visit: http://api-timesheet.firsteconomy.com/register-developer
   - Or run: python simple_token_creator.py

2. For each developer:
   - Enter their name (e.g., "john_doe")
   - Generate a token starting with "AWToken_"
   - Save these credentials

🟡 IF YOU HAVE DEVELOPERS BUT NO ACTIVITY:
------------------------------------------
1. Check if sync scripts are running:
   - Linux: ps aux | grep sync.sh
   - Windows: Check Task Manager for sync.ps1

2. Start sync on developer machines:
   - Linux: ./sync.sh "developer_name" "api_token"
   - Windows: .\\sync.ps1

3. Verify ActivityWatch is running:
   - Visit: http://localhost:5600
   - Should see ActivityWatch dashboard

4. Check sync endpoint:
   - curl http://api-timesheet.firsteconomy.com/api/sync
   - Should not return 404

🟢 IF YOU HAVE DATA BUT CORS ERRORS:
-------------------------------------
1. Fix Apache configuration:
   - SSH to server
   - Edit: /etc/apache2/sites-enabled/timesheet-backend.conf
   - Remove ALL "Header set Access-Control-Allow-Origin" lines
   - Restart: sudo systemctl restart apache2

2. Test the fix:
   - Open browser console
   - Visit: http://timesheet.firsteconomy.com
   - Should see no CORS errors

🔵 TO ADD TEST DATA:
--------------------
1. Run: python add_sample_data.py
2. This adds sample activities for testing
3. Your dashboard will show example data

📈 TO VIEW YOUR DATA:
---------------------
1. Using pgAdmin:
   - Connect to localhost:5432
   - Database: timesheet
   - Run queries from check_database.sql

2. Using Python:
   - python full_db_check.py
   - python view_saved_data.py

3. Using Web Interface:
   - http://timesheet.firsteconomy.com (Dashboard)
   - http://api-timesheet.firsteconomy.com/developers-list (Developer List)

🔧 TROUBLESHOOTING:
-------------------
Q: Database connection failed?
A: Check PostgreSQL is running:
   - Windows: Check Services for "postgresql-x64-16"
   - Linux: sudo systemctl status postgresql

Q: Sync not working?
A: Check logs:
   - Developer machine: ~/activitywatch_sync.log
   - Server: pm2 logs timesheet-backend

Q: No data showing up?
A: Verify chain:
   1. ActivityWatch running on developer machine
   2. Sync script running and no errors
   3. Server endpoint /api/sync working
   4. Check database has records

📞 QUICK COMMANDS:
------------------
# Check all developers
psql -U postgres -d timesheet -c "SELECT * FROM developers;"

# Check today's activity  
psql -U postgres -d timesheet -c "SELECT developer_id, COUNT(*), SUM(duration)/3600.0 as hours FROM activity_records WHERE DATE(timestamp) = CURRENT_DATE GROUP BY developer_id;"

# Check sync status
psql -U postgres -d timesheet -c "SELECT developer_id, MAX(timestamp) FROM activity_records GROUP BY developer_id;"

# Run full check
python full_db_check.py
""")
