# 🗄️ Database Guide - Where Your Data is Stored

## 📊 Database Overview

**Database Type**: PostgreSQL  
**Database Name**: `timesheet`  
**Connection**: `postgresql://postgres:asdf1234@localhost:5432/timesheet`  
**Total Records**: 753 activity records  
**Total Time Tracked**: 11.29 hours  

## 📋 Main Tables

### 1. `users` Table
**Purpose**: Stores user accounts  
**Records**: 2 users  
**Columns**:
- `id` - User ID (Primary Key)
- `username` - Login username
- `email` - User email
- `hashed_password` - Encrypted password
- `created_at` - Account creation date

**Your Data**:
- User ID 1: testuser (test@example.com) - 0 activities
- User ID 2: admin (admin@timesheet.com) - 753 activities

### 2. `activity_records` Table ⭐ **MAIN DATA TABLE**
**Purpose**: Stores all your activity tracking data  
**Records**: 753 activities  
**Columns**:
- `id` - Record ID (Primary Key)
- `user_id` - Links to users table
- `application_name` - App name (chrome.exe, Cursor.exe, etc.)
- `window_title` - Window title text
- `url` - Website URL (for browser activities)
- `file_path` - File being worked on (for development)
- `database_connection` - Database connection info
- `specific_process` - Process details
- `detailed_activity` - Human-readable description
- `category` - Activity category (development, browser, etc.)
- `duration` - Time spent in seconds
- `timestamp` - When the activity occurred
- `created_at` - When record was saved

## 🔍 How to Check Your Data

### Option 1: DataGrip (Recommended - You Already Have This!)
1. Open DataGrip
2. Connect to: `postgresql://postgres:asdf1234@localhost:5432/timesheet`
3. Navigate to `timesheet` database → `public` schema → `activity_records` table
4. Right-click → "View Data" to see all records

**Useful Queries**:
```sql
-- See all your activities
SELECT * FROM activity_records WHERE user_id = 2 ORDER BY timestamp DESC;

-- Today's activities
SELECT application_name, window_title, duration, timestamp 
FROM activity_records 
WHERE user_id = 2 AND DATE(timestamp) = CURRENT_DATE;

-- Time by category
SELECT category, SUM(duration)/3600 as hours, COUNT(*) as activities
FROM activity_records 
WHERE user_id = 2 
GROUP BY category 
ORDER BY hours DESC;

-- Files you've worked on
SELECT file_path, SUM(duration)/3600 as hours, COUNT(*) as sessions
FROM activity_records 
WHERE user_id = 2 AND file_path IS NOT NULL
GROUP BY file_path 
ORDER BY hours DESC;
```

### Option 2: Python Scripts (Easy to Use)
```bash
# Navigate to backend folder
cd E:\timesheet\timesheet\backend

# View database overview
python inspect_database.py

# Simple queries and stats
python query_database.py

# Check specific data
python view_saved_data.py
```

### Option 3: Command Line (PostgreSQL)
```bash
# Connect to database
psql -h localhost -U postgres -d timesheet

# List tables
\dt

# View your data
SELECT * FROM activity_records WHERE user_id = 2 LIMIT 10;
```

## 📈 Your Current Data Summary

**Total Statistics**:
- **753 activity records** tracked
- **11.29 hours** of total time
- **Date range**: September 5 - September 14, 2025
- **Average per day**: 1.59 hours

**Top Applications**:
1. **Chrome**: 4.32h (169 activities) - Web browsing
2. **Cursor**: 2.74h (136 activities) - Code development  
3. **Unknown**: 2.00h (272 activities) - System activities
4. **LockApp**: 1.51h (82 activities) - Screen lock/breaks

**Recent Files Worked On**:
- `timesheet/productivity_calculator.py` - 0.31h
- `timesheet/activitywatch_client.py` - 0.24h
- `timesheet/test_activitywatch.py` - 0.12h

## 🛠️ Data Storage Locations

### Database Files
- **PostgreSQL Data**: Managed by PostgreSQL server
- **Connection Config**: `E:\timesheet\timesheet\.env`
- **Database Models**: `E:\timesheet\timesheet\backend\models.py`

### Application Files
- **Backend Code**: `E:\timesheet\timesheet\backend\`
- **Frontend Code**: `E:\timesheet\timesheet\frontend\`
- **Database Scripts**: `E:\timesheet\timesheet\backend\*_database.py`

## 🔧 Backup & Export

### Export Your Data
```sql
-- Export all your activities to CSV
COPY (
    SELECT application_name, window_title, category, duration, timestamp, file_path, url
    FROM activity_records 
    WHERE user_id = 2 
    ORDER BY timestamp
) TO 'C:\your_activities.csv' WITH CSV HEADER;
```

### Backup Database
```bash
# Full database backup
pg_dump -h localhost -U postgres timesheet > timesheet_backup.sql

# Restore from backup
psql -h localhost -U postgres timesheet < timesheet_backup.sql
```

## 🎯 Key Insights from Your Data

1. **Most Productive**: You spend the most time in development (Cursor) and research (Chrome)
2. **Work Pattern**: Average 1.59h tracked per day over the last week
3. **File Focus**: Most time spent on productivity calculator and ActivityWatch integration
4. **Categories**: Development, browser, and system activities are your main categories

## 📱 Real-time Access

Your timesheet application at `http://localhost:3000` shows this data in real-time with:
- **Daily working hours** with color coding
- **Productivity analysis** with smart recommendations
- **Activity breakdown** by category and application
- **Detailed logs** with file paths and URLs

All this data is automatically synced from ActivityWatch and stored permanently in your PostgreSQL database!








