@echo off
echo Checking Timesheet Database...
echo ==============================
echo.

cd /d E:\timesheet\timesheet_new\backend

echo Running database check...
python quick_db_check.py

echo.
echo ==============================
echo.
echo For detailed data, you can:
echo 1. Run: python check_developer_data.py
echo 2. Or use pgAdmin with the queries in check_database.sql
echo.
pause
