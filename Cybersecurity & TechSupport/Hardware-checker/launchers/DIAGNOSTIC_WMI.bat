@echo off
title PC Hardware Checker - WMI Debug Mode
echo ================================================================
echo           PC Hardware Checker - WMI Debug Mode
echo ================================================================
echo.
echo This mode will help diagnose and fix WMI-related issues.
echo.

REM Ensure we're in the correct directory
cd /d "%~dp0\.."
echo Working directory: %CD%
echo.

REM Check if Python is installed
echo [1/4] Checking Python installation...
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

REM Check if required packages are installed
echo [2/4] Checking required packages...
python -c "import psutil, tkinter, wmi" >nul 2>&1
if errorlevel 1 (
    echo Installing WMI package...
    pip install WMI
    echo Installing other packages...
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
echo.

REM Run WMI diagnostic
echo [3/4] Running WMI diagnostic...
echo.
if exist "tools\wmi_diagnostic.py" (
    python tools\wmi_diagnostic.py
) else (
    echo ERROR: tools\wmi_diagnostic.py not found
    echo Make sure all files are in the correct folder structure
    pause
    exit /b 1
)
echo.

REM Test motherboard detection specifically
echo [4/4] Testing motherboard detection...
echo.
python -c "import sys; sys.path.append('src'); from hardware_detector import HardwareDetector; hd = HardwareDetector(); print('=== MOTHERBOARD TEST ==='); mb = hd.get_motherboard_info(); [print(f'{k}: {v}') for k, v in mb.items()]"
echo.

echo ================================================================
echo                    Debug Complete
echo ================================================================
echo.
echo If motherboard detection is working here but not in the GUI,
echo the issue may be related to threading or GUI context.
echo.
echo Try running with administrator privileges for best results:
echo Right-click this file and select "Run as administrator"
echo.
pause
