@echo off
title PC Hardware Checker - WMI Repair Utility
echo ================================================================
echo            PC Hardware Checker - WMI Repair Utility
echo ================================================================
echo.
echo This utility helps fix WMI (Windows Management) issues that
echo prevent hardware detection from working properly.
echo.
echo IMPORTANT: This must be run as administrator!
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ NOT running as administrator
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Running with administrator privileges
)

echo.

REM Ensure we're in the correct directory
cd /d "%~dp0\.."
echo Working directory: %CD%
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first, then run this repair utility
    pause
    exit /b 1
) else (
    python --version
    echo ✓ Python found
)
echo.

REM Check if the repair tool exists
if not exist "tools\wmi_repair.py" (
    echo ERROR: tools\wmi_repair.py not found
    echo Make sure all files are in the correct folder structure
    pause
    exit /b 1
)

REM Run the WMI repair utility
echo Starting WMI Repair Utility...
echo.
python tools\wmi_repair.py

echo.
echo ================================================================
echo                    Repair Process Complete
echo ================================================================
echo.
echo After repair, try running the hardware checker again:
echo • Use "run_admin_simple.bat" for best results
echo • Or use "debug_wmi.bat" to test WMI functionality
echo.
pause
