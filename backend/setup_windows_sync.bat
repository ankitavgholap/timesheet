@echo off
REM Windows setup script for ActivityWatch Data Syncing

echo 🚀 Setting up ActivityWatch Data Sync for Windows
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not found in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check current directory
if not exist "requirements.txt" (
    echo ❌ Please run this script from the client_sync directory
    echo Current directory should contain requirements.txt
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment and install dependencies
echo 📥 Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Copy environment template if .env doesn't exist
if not exist ".env" (
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo 📝 Created .env file from template
    ) else (
        echo 📝 Creating .env file...
        echo # ActivityWatch Sync Configuration > .env
        echo SERVER_URL=http://localhost:8000/api/v1 >> .env
        echo DEVELOPER_ID=ankita_gholap >> .env
        echo API_TOKEN=your_token_here >> .env
        echo ACTIVITYWATCH_HOST=http://localhost:5600 >> .env
        echo SYNC_INTERVAL_MINUTES=15 >> .env
        echo LOG_LEVEL=INFO >> .env
    )
    echo ⚠️  Please edit .env file with your server details and token
) else (
    echo ℹ️  .env file already exists
)

REM Create Windows service script
echo 📋 Creating Windows service scripts...

echo @echo off > start_sync.bat
echo call venv\Scripts\activate.bat >> start_sync.bat
echo python activitywatch_sync.py --continuous >> start_sync.bat

echo @echo off > test_sync.bat
echo call venv\Scripts\activate.bat >> test_sync.bat
echo python activitywatch_sync.py --test >> test_sync.bat

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your server URL and token
echo 2. Test connection: test_sync.bat
echo 3. Run continuous sync: start_sync.bat
echo.
echo To run automatically at startup, add start_sync.bat to Windows startup folder
pause
