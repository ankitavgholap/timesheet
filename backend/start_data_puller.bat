@echo off
cd /d "/e/timesheet/timesheet_new/backend"
python automated_data_puller.py >> logs/cron.log 2>&1
