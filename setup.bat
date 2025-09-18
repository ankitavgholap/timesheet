@echo off
echo Setting up Timesheet Application...

echo.
echo 1. Setting up Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo 2. Installing Python dependencies...
pip install -r requirements.txt

echo.
echo 3. Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit it with your settings.
) else (
    echo .env file already exists.
)

echo.
echo 4. Setting up frontend...
cd frontend
npm install
cd ..

echo.
echo Setup complete!
echo.
echo To run the application:
echo 1. Make sure ActivityWatch is running
echo 2. Run: run_backend.bat
echo 3. In another terminal, run: run_frontend.bat
echo 4. Open http://localhost:3000 in your browser
echo.
pause
