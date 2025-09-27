"""
Simple database info without connection
"""
print("📊 TIMESHEET DATABASE INFORMATION")
print("=" * 50)

print("\n🔧 Database Configuration:")
print("  Database: timesheet")
print("  Host: localhost")
print("  Port: 5432")
print("  User: postgres")

print("\n📋 Main Tables:")
print("  1. developers - Stores developer information")
print("  2. activity_records - Stores ActivityWatch data")

print("\n🔍 To Check Your Data:")
print("\n1. Using pgAdmin:")
print("   - Connect to localhost:5432")
print("   - Database: timesheet")
print("   - Run queries from check_database.sql")

print("\n2. Using Command Line:")
print("   psql -U postgres -d timesheet")
print("   Then run: \\dt (to list tables)")
print("            SELECT * FROM developers;")
print("            SELECT * FROM activity_records LIMIT 10;")

print("\n3. Using Python Scripts:")
print("   python quick_db_check.py")
print("   python check_developer_data.py")

print("\n📝 Common Queries:")
print("""
-- Check all developers
SELECT developer_id, name, api_token, created_at 
FROM developers;

-- Check today's activity
SELECT developer_id, COUNT(*), SUM(duration)/3600.0 as hours
FROM activity_records 
WHERE DATE(timestamp) = CURRENT_DATE
GROUP BY developer_id;

-- Check if sync is working
SELECT developer_id, MAX(timestamp) as last_sync
FROM activity_records
GROUP BY developer_id;
""")

print("\n💡 Troubleshooting:")
print("  - No data? Check if sync.sh is running on developer machines")
print("  - CORS errors? Fix Apache config (remove duplicate headers)")
print("  - Can't connect? Check if PostgreSQL is running")
