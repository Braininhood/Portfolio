@echo off
title PC Hardware Checker - EXE Builder
echo ================================================================
echo        PC Hardware Checker Professional - EXE Builder
echo ================================================================
echo.
echo This will create a standalone EXE file that runs without Python.
echo.

REM Check if PyInstaller is installed
echo [1/4] Checking PyInstaller installation...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller --user
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        echo Please run: pip install pyinstaller --user
        pause
        exit /b 1
    )
) else (
    echo ✓ PyInstaller found
)

REM Install all required packages first
echo.
echo [2/4] Installing all required packages...
pip install -r requirements.txt --user
pip install -r requirements_testing.txt --user

REM Clean previous builds
echo.
echo [3/4] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build the EXE
echo.
echo [4/4] Building standalone EXE file...
echo This may take several minutes...
echo.

pyinstaller build_exe.spec

if errorlevel 1 (
    echo.
    echo ❌ BUILD FAILED
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ BUILD SUCCESSFUL!
    echo.
    echo EXE file created: dist\PC_Hardware_Checker_Professional.exe
    echo.
    echo You can now copy this EXE file to any Windows computer
    echo and it will run without requiring Python installation.
    echo.
    echo File size and location:
    dir "dist\PC_Hardware_Checker_Professional.exe"
    echo.
    echo Opening dist folder...
    start dist
)

pause
