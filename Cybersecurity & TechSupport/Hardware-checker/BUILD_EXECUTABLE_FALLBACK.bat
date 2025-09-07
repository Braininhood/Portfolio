@echo off
title PC Hardware Checker - Simple EXE Builder
echo ================================================================
echo     PC Hardware Checker Professional - Simple EXE Builder
echo ================================================================
echo.
echo This creates a standalone EXE using PyInstaller's auto-detection.
echo.

REM Check if PyInstaller is installed
echo [1/3] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller --user
) else (
    echo ✓ PyInstaller ready
)

REM Install required packages
echo.
echo [2/3] Installing packages...
pip install -r requirements.txt --user

REM Clean and build
echo.
echo [3/3] Building EXE (simple method)...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Try with detailed spec file first
if exist "build_exe.spec" (
    echo Trying with detailed spec file...
    pyinstaller build_exe.spec
) else (
    echo Using simple method...
    pyinstaller --onefile --windowed --name "PC_Hardware_Checker_Professional" --add-data "src;src" --hidden-import hardware_detector --hidden-import gui_components --hidden-import hardware_stress_tester --hidden-import stress_test_gui --hidden-import professional_monitor --hidden-import windows_temperature --hidden-import formatting_utils src/main.py
)

if errorlevel 1 (
    echo ❌ Windowed build failed, trying with console enabled...
    pyinstaller --onefile --console --name "PC_Hardware_Checker_Professional" --add-data "src;src" --hidden-import hardware_detector --hidden-import gui_components --hidden-import hardware_stress_tester --hidden-import stress_test_gui --hidden-import professional_monitor --hidden-import windows_temperature --hidden-import formatting_utils src/main.py
)

if exist "dist\PC_Hardware_Checker_Professional.exe" (
    echo.
    echo ✅ BUILD SUCCESSFUL!
    echo EXE location: dist\PC_Hardware_Checker_Professional.exe
    start dist
) else (
    echo ❌ Build failed. Check error messages above.
)

pause
