@echo off
title PC Hardware Checker
echo ================================================================
echo                 PC Hardware Checker
echo ================================================================
echo Starting PC Hardware Checker...
echo.

REM Ensure we're in the correct directory (go up one level from launchers)
cd /d "%~dp0\.."
echo Working directory: %CD%
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    python --version
    echo ✓ Python found
)

REM Check if required packages are installed
echo Checking required packages...
python -c "import psutil, tkinter" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
) else (
    echo ✓ All packages available
)

REM Check if main.py exists in src directory
if not exist "src\main.py" (
    echo ERROR: src\main.py not found
    echo Make sure you're running this from the PC Hardware Checker folder
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Run the application
echo Starting application...
echo.
python src\main.py

if errorlevel 1 (
    echo.
    echo ⚠️ Application encountered an error.
    echo.
    echo Troubleshooting tips:
    echo 1. Make sure all files are in the correct folders
    echo 2. Try running "install.bat" first  
    echo 3. For enhanced detection, try "run_admin_simple.bat"
    echo 4. Check docs\README.md for more help
    echo.
    pause
) else (
    echo.
    echo ✓ Application closed successfully.
    echo.
)
