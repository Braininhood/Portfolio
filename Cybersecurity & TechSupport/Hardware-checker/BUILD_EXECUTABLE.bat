@echo off
title PC Hardware Checker - EXE Builder (Recommended)
echo ================================================================
echo      PC Hardware Checker Professional - EXE Builder
echo ================================================================
echo.
echo Building with tkinter only (excluding Qt packages)...
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build excluding problematic packages
echo Building standalone EXE (tkinter only, no Qt)...
pyinstaller --onefile --console --name "PC_Hardware_Checker_Professional" ^
    --add-data "src;src" ^
    --exclude-module PyQt5 ^
    --exclude-module PyQt6 ^
    --exclude-module PySide2 ^
    --exclude-module PySide6 ^
    --exclude-module scipy ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module pytest ^
    src/main.py

if exist "dist\PC_Hardware_Checker_Professional.exe" (
    echo.
    echo ✅ BUILD SUCCESSFUL!
    echo EXE location: dist\PC_Hardware_Checker_Professional.exe
    echo File size:
    dir "dist\PC_Hardware_Checker_Professional.exe"
    echo.
    echo Testing the EXE...
    echo Starting application to verify it works...
    echo.
    start "Hardware Checker Test" "dist\PC_Hardware_Checker_Professional.exe"
    echo.
    echo ✅ EXE test launched! Check if the application opens correctly.
) else (
    echo ❌ Build failed. Check error messages above.
)

pause
