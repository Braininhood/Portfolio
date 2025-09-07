@echo off
title PC Hardware Checker - Simple Stress Testing Installation
echo ================================================================
echo     PC Hardware Checker - Simple Stress Testing Installation
echo ================================================================
echo.
echo Installing minimal stress testing libraries for maximum compatibility
echo.

REM Check if Python is installed
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
) else (
    python --version
    echo ✓ Python found
)
echo.

REM Check essential packages
echo [2/3] Checking essential packages...
python -c "import psutil, wmi" >nul 2>&1
if errorlevel 1 (
    echo Installing essential packages...
    pip install psutil wmi pywin32 --user
) else (
    echo ✓ Essential packages available
)
echo.

REM Install minimal stress testing libraries
echo [3/3] Installing stress testing libraries...
echo.

echo Installing numpy (essential for stress testing)...
pip install numpy --user
if errorlevel 1 (
    echo WARNING: numpy installation failed
    echo Stress testing will use basic methods only
) else (
    echo ✓ numpy installed successfully
)

echo Installing py-cpuinfo (for detailed CPU information)...
pip install py-cpuinfo --user
if errorlevel 1 (
    echo WARNING: py-cpuinfo installation failed
    echo Using basic CPU detection instead
) else (
    echo ✓ py-cpuinfo installed successfully
)

echo.
echo ================================================================
echo           Simple Stress Testing Installation Complete!
echo ================================================================
echo.
echo Installed stress testing capabilities:
echo ✓ CPU stress testing (mathematical operations)
echo ✓ Memory stress testing (allocation patterns)  
echo ✓ Disk performance testing (read/write operations)
echo ✓ System monitoring during tests
echo ✓ Real-time progress tracking
echo.
echo Note: This is a simplified installation that avoids
echo problematic packages while providing core functionality.
echo.
echo To start: Double-click "run_admin_simple.bat"
echo Then click "🔥 Stress Tests" in the application
echo.
pause
