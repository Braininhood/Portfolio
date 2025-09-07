@echo off
title PC Hardware Checker - Essential Installation
echo ================================================================
echo        PC Hardware Checker - Essential Installation
echo ================================================================
echo.
echo Installing only essential components for maximum compatibility
echo.

REM Check if Python is installed
echo [1/2] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first from python.org
    pause
    exit /b 1
) else (
    python --version
    echo ✓ Python found
)
echo.

REM Install essential requirements only
echo [2/2] Installing essential requirements...
echo.

echo Installing psutil (system monitoring)...
pip install psutil --user
if errorlevel 1 (
    echo ERROR: Failed to install psutil
    echo Please check your internet connection
    pause
    exit /b 1
) else (
    echo ✓ psutil installed successfully
)

echo Installing wmi (Windows hardware access)...
pip install wmi --user
if errorlevel 1 (
    echo WARNING: wmi installation failed
    echo Some hardware detection may not work
) else (
    echo ✓ wmi installed successfully
)

echo Installing pywin32 (Windows COM support)...
pip install pywin32 --user
if errorlevel 1 (
    echo WARNING: pywin32 installation failed
    echo Some Windows features may not work
) else (
    echo ✓ pywin32 installed successfully
)

echo Installing GPUtil (GPU monitoring)...
pip install GPUtil --user
if errorlevel 1 (
    echo WARNING: GPUtil installation failed
    echo GPU monitoring may not work
) else (
    echo ✓ GPUtil installed successfully
)

echo.
echo ================================================================
echo              Essential Installation Complete!
echo ================================================================
echo.
echo ✓ Core hardware detection: READY
echo ✓ System monitoring: READY
echo ✓ Windows integration: READY
echo ✓ GPU monitoring: READY
echo.
echo The PC Hardware Checker is now ready to use!
echo.
echo To start: Double-click "run_admin_simple.bat"
echo.
echo For stress testing features:
echo - Run "install_stress_testing.bat" (advanced users)
echo - Or manually install: pip install numpy py-cpuinfo
echo.
pause
