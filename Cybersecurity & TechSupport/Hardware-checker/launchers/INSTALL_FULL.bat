@echo off
title PC Hardware Checker - Installation
echo ================================================================
echo              PC Hardware Checker - Installation
echo ================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Note: Running without administrator privileges
    echo Some features may show limited information
    echo.
)

REM Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not found in PATH
    echo.
    echo Please install Python 3.7 or higher:
    echo 1. Go to https://python.org/downloads/
    echo 2. Download the latest Python version
    echo 3. During installation, CHECK "Add Python to PATH"
    echo 4. Run this installer again after Python is installed
    echo.
    pause
    exit /b 1
) else (
    python --version
    echo Python found successfully!
)
echo.

REM Check pip
echo [2/4] Checking pip package manager...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not found
    echo Please reinstall Python with pip included
    pause
    exit /b 1
) else (
    echo pip found successfully!
)
echo.

REM Install required packages
echo [3/4] Installing required packages...
echo This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some packages
    echo This might be due to:
    echo - Network connectivity issues
    echo - Permission restrictions
    echo - Missing build tools
    echo.
    echo Try running as administrator or check your internet connection
    pause
    exit /b 1
) else (
    echo All packages installed successfully!
)
echo.

REM Test the installation
echo [4/4] Testing installation...
python -c "import psutil, tkinter; print('All modules imported successfully')" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some modules may not be working properly
    echo The application may still work with limited functionality
) else (
    echo Installation test passed!
)
echo.

echo ================================================================
echo              Installation Complete!
echo ================================================================
echo.
echo You can now run PC Hardware Checker by:
echo 1. Double-clicking "run_admin_simple.bat" (recommended)
echo 2. Double-clicking "run.bat" (standard mode)
echo 3. Or running "python src\main.py" in command prompt
echo.
echo If you encounter any issues:
echo - Try running as administrator
echo - Check that Python and pip are in your PATH
echo - Ensure you have an internet connection during installation
echo.
pause
