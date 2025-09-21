# 🔧 Database Connection Fix Guide

## 🚨 Issue Identified
Your application is trying to connect to:
`db.ckpirxedodqdewcpdijx.supabase.co:5432`

But getting: **"Network is unreachable"**

## 🎯 Quick Solutions (Choose One)

### **Option 1: Fix Supabase Connection (Recommended)**

#### **Step 1.1: Check Your .env Database URL**
```bash
cd /var/www/html/timesheet/backend
cat .env | grep DATABASE_URL
```

Your DATABASE_URL should look like:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.ckpirxedodqdewcpdijx.supabase.co:5432/postgres
```

#### **Step 1.2: Verify Supabase Connection**
```bash
# Test connection manually
psql "postgresql://postgres:YOUR_PASSWORD@db.ckpirxedodqdewcpdijx.supabase.co:5432/postgres"
```

If this fails, the issue might be:
- ❌ **Supabase project paused** (free tier limitation)
- ❌ **Wrong password** in DATABASE_URL
- ❌ **Network/firewall blocking** connection
- ❌ **Supabase project deleted** or moved

#### **Step 1.3: Check Supabase Dashboard**
1. Go to [supabase.com](https://supabase.com)
2. Login to your account
3. Check if your project is **active** (not paused)
4. Get the correct connection string from Settings → Database

#### **Step 1.4: Update Connection String**
```bash
# Edit your .env file
nano /var/www/html/timesheet/backend/.env

# Update DATABASE_URL with correct values from Supabase dashboard
DATABASE_URL=postgresql://postgres:CORRECT_PASSWORD@db.ckpirxedodqdewcpdijx.supabase.co:5432/postgres
```

### **Option 2: Switch to Local PostgreSQL (Fast Alternative)**

#### **Step 2.1: Install Local PostgreSQL**
```bash
# Install PostgreSQL locally
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### **Step 2.2: Create Local Database**
```bash
# Switch to postgres user and create database
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE timesheet;
CREATE USER timesheet_user WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE timesheet TO timesheet_user;
ALTER USER timesheet_user CREATEDB;
\\q
```

#### **Step 2.3: Update .env for Local Database**
```bash
# Edit .env file
nano /var/www/html/timesheet/backend/.env

# Replace DATABASE_URL with local connection:
DATABASE_URL=postgresql://timesheet_user:secure_password_123@localhost:5432/timesheet
```

### **Option 3: Use SQLite (Simplest for Testing)**

#### **Step 3.1: Update .env for SQLite**
```bash
# Edit .env file
nano /var/www/html/timesheet/backend/.env

# Replace DATABASE_URL with SQLite:
DATABASE_URL=sqlite:///./timesheet.db
```

#### **Step 3.2: Install SQLite Dependencies**
```bash
cd /var/www/html/timesheet/backend
source venv/bin/activate
pip install sqlite3
```

## 🚀 After Fixing Database Connection

### **Step 1: Test Database Connection**
```bash
cd /var/www/html/timesheet/backend
source venv/bin/activate

# Test the connection
python -c "
from database import engine
try:
    conn = engine.connect()
    print('✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### **Step 2: Run Database Migration**
```bash
# Run the migration to add developer_id column
python ../database_migration.py
```

Expected output:
```
✅ Connected to database successfully
✅ Developers table created/verified
✅ Added developer_id column to activity_records
✅ Database migration completed successfully
```

### **Step 3: Add Stateless Integration**
```bash
# Edit main.py
nano main.py
```

Add these lines:
```python
# Add this import at the top with other imports
from stateless_webhook import router as stateless_router

# Add this line after your existing middleware/router setup
app.include_router(stateless_router, prefix="/api/v1", tags=["stateless-webhook"])
```

### **Step 4: Update Environment Variables**
```bash
# Edit .env file
nano .env

# Add these new variables:
MASTER_SECRET=your-master-secret-for-token-generation-keep-secure
SERVER_URL=https://your-domain.com
```

### **Step 5: Restart the Application**
```bash
# If using PM2
pm2 restart timesheet-backend

# If running manually
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Step 6: Test the Fix**
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Should return:
{
  "status": "healthy",
  "mode": "stateless",
  "timestamp": "...",
  "message": "ActivityWatch webhook endpoint is running (stateless mode)"
}
```

## 🔍 Troubleshooting Specific Issues

### **If Supabase Connection Still Fails:**

#### **Check Supabase Project Status**
1. Login to [supabase.com](https://supabase.com)
2. Select your project
3. Check if it shows "Project is paused" message
4. If paused, click "Resume project"

#### **Get Fresh Connection String**
1. Go to Settings → Database
2. Copy the connection string
3. Make sure to replace `[YOUR-PASSWORD]` with actual password
4. Update your .env file

#### **Check Network Connectivity**
```bash
# Test if you can reach Supabase
ping db.ckpirxedodqdewcpdijx.supabase.co

# Test port connectivity
telnet db.ckpirxedodqdewcpdijx.supabase.co 5432
```

### **If Local PostgreSQL Installation Fails:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo journalctl -u postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### **If SQLite Option Chosen:**
```bash
# Check if SQLite database is created
ls -la /var/www/html/timesheet/backend/timesheet.db

# Test SQLite connection
sqlite3 /var/www/html/timesheet/backend/timesheet.db ".tables"
```

## ✅ **Verification Steps**

After fixing the database connection:

1. **Database Connection Test**
   ```bash
   python -c "from database import engine; print('✅ DB Connected!' if engine.connect() else '❌ Failed')"
   ```

2. **Application Starts Without Errors**
   ```bash
   python -m uvicorn main:app --reload --port 8000
   # Should start without the psycopg2.OperationalError
   ```

3. **Health Endpoint Responds**
   ```bash
   curl http://localhost:8000/api/v1/health
   # Should return healthy status
   ```

4. **Database Tables Created**
   ```bash
   # For PostgreSQL:
   psql $DATABASE_URL -c "\\dt"
   
   # For SQLite:
   sqlite3 timesheet.db ".tables"
   ```

## 🚨 **Common Causes & Solutions**

| Issue | Cause | Solution |
|-------|-------|----------|
| Network unreachable | Supabase project paused | Resume project in dashboard |
| Connection refused | Wrong password | Get fresh connection string |
| Timeout | Firewall blocking | Check server firewall rules |
| SSL error | SSL mode mismatch | Add `?sslmode=require` to URL |
| Host not found | Incorrect hostname | Verify URL in Supabase dashboard |

Choose the database option that works best for your setup, then continue with the stateless ActivityWatch integration!
