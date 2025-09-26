@echo off
title ActivityWatch Sync - PowerShell Version
echo Starting ActivityWatch sync...
echo This runs using Windows PowerShell (no Python needed)
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Check if PowerShell is available (it should be on all Windows systems)
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell not found
    pause
    exit /b 1
)

REM Run the PowerShell sync script
powershell -ExecutionPolicy Bypass -File "sync.ps1"
pause