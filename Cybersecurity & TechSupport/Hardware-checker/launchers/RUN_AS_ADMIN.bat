@echo off
title PC Hardware Checker - Enhanced Mode
echo ================================================================
echo         PC Hardware Checker - Enhanced Mode
echo ================================================================
echo.
echo This will run the hardware checker with enhanced capabilities.
echo If you see permission warnings, right-click this file and
echo select "Run as administrator" for maximum hardware detection.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Running with administrator privileges
    echo   Enhanced hardware detection available!
) else (
    echo ℹ️ Running in standard mode
    echo   For maximum detection, right-click and "Run as administrator"
)
echo.

REM Ensure we're in the correct directory
cd /d "%~dp0\.."
echo Working directory: %CD%
echo.

REM Check if Python is installed
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    python --version
    echo ✓ Python found successfully!
)
echo.

REM Check if required packages are installed
echo [2/3] Checking required packages...
python -c "import psutil, tkinter" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
) else (
    echo ✓ All packages available
)
echo.

REM Check if main.py exists
echo [3/3] Starting PC Hardware Checker...
if not exist "src\main.py" (
    echo ERROR: src\main.py not found in current directory
    echo Make sure you're running this from the PC Hardware Checker folder
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting application...
echo.
python src\main.py

if errorlevel 1 (
    echo.
    echo ⚠️ Application encountered an error.
    echo.
    echo Troubleshooting tips:
    echo 1. Make sure all files are in the same folder structure
    echo 2. Try running "install.bat" first
    echo 3. Check that Python is properly installed
    echo 4. For support, check docs\README.md
    echo.
    pause
) else (
    echo.
    echo ✓ Application closed successfully.
    echo.
)
