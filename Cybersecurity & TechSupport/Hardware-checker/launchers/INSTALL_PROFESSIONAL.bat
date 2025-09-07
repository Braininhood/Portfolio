@echo off
title PC Hardware Checker - Stress Testing Installation
echo ================================================================
echo        PC Hardware Checker - Stress Testing Installation
echo ================================================================
echo.
echo This will install additional Python libraries for hardware
echo stress testing capabilities.
echo.

REM Check if Python is installed
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first using install.bat
    pause
    exit /b 1
) else (
    python --version
    echo ✓ Python found
)
echo.

REM Install basic requirements first
echo [2/3] Installing basic requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install basic requirements
    echo Please check your internet connection
    pause
    exit /b 1
) else (
    echo ✓ Basic requirements installed
)
echo.

REM Install stress testing requirements
echo [3/3] Installing stress testing libraries...
echo This may take several minutes...
echo.

REM Update pip first
echo Updating pip...
python -m pip install --upgrade pip --user

REM Install essential stress testing libraries one by one
echo Installing essential stress testing libraries...

echo Installing numpy...
pip install numpy --user
if errorlevel 1 (
    echo WARNING: numpy installation failed
    echo Some stress tests may not work optimally
) else (
    echo ✓ numpy installed successfully
)

echo Installing py-cpuinfo...
pip install py-cpuinfo --user
if errorlevel 1 (
    echo WARNING: py-cpuinfo installation failed
) else (
    echo ✓ py-cpuinfo installed successfully
)

echo Installing optional libraries (errors are normal)...

REM Try to install optional libraries (don't fail if they don't work)
pip install scipy --user >nul 2>&1
if errorlevel 1 (
    echo INFO: scipy not installed (optional)
) else (
    echo ✓ scipy installed successfully
)

pip install memory-profiler --user >nul 2>&1
if errorlevel 1 (
    echo INFO: memory-profiler not installed (optional)
) else (
    echo ✓ memory-profiler installed successfully
)

echo.
echo ================================================================
echo              Stress Testing Installation Complete!
echo ================================================================
echo.
echo Installed stress testing capabilities:
echo ✓ CPU stress testing with multiple intensity levels
echo ✓ Memory stress testing and stability checks  
echo ✓ Disk performance and endurance testing
echo ✓ GPU stress testing capabilities
echo ✓ Comprehensive system stress testing
echo ✓ Real-time monitoring during tests
echo ✓ Performance benchmarking and reports
echo.
echo You can now run the hardware checker and access the
echo "Stress Tests" tab for comprehensive hardware testing!
echo.
echo To start: Double-click "run_admin_simple.bat"
echo.
pause
