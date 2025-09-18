@echo off
echo Starting Timesheet Application...
echo.

echo Checking if ActivityWatch is running...
curl -s http://localhost:5600 >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ActivityWatch is not running!
    echo Please start ActivityWatch first for real-time data tracking.
    echo You can still use the app with sample data.
    echo.
)

echo Starting backend server...
start "Backend Server" cmd /k "call venv\Scripts\activate.bat && python run_backend.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting frontend...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo Application is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause >nul
