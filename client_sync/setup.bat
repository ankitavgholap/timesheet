@echo off
REM Setup script for ActivityWatch Sync Client on Windows

echo 🚀 Setting up ActivityWatch Sync Client...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if ActivityWatch is running
curl -s http://localhost:5600/api/0/buckets/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  ActivityWatch doesn't seem to be running on localhost:5600
    echo Please start ActivityWatch before running the sync client
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment and install dependencies
echo 📥 Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Copy environment template
if not exist .env (
    copy .env.template .env
    echo 📝 Created .env file from template
    echo ⚠️  Please edit .env file with your server details and credentials
) else (
    echo ℹ️  .env file already exists
)

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your server URL and credentials
echo 2. Test connection: python activitywatch_sync.py --test
echo 3. Run sync: python activitywatch_sync.py --continuous
echo.
echo Or to run as a Windows service:
echo   setup_service.bat

pause
