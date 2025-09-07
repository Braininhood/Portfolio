@echo off
title PC Hardware Checker Professional - Portable EXE Launcher
echo ================================================================
echo     PC Hardware Checker Professional - Portable EXE
echo ================================================================
echo.
echo This will run the standalone EXE version that works without Python.
echo.

if exist "dist\PC_Hardware_Checker_Professional.exe" (
    echo ✅ Portable EXE found
    echo.
    echo Starting PC Hardware Checker Professional (Standalone)...
    echo.
    start "PC Hardware Checker Professional" "dist\PC_Hardware_Checker_Professional.exe"
    echo ✅ Application launched!
    echo.
    echo 📖 For deployment information, see dist\DEPLOYMENT_GUIDE.txt
    echo 📋 For user instructions, see dist\README_PORTABLE.txt
) else (
    echo ❌ Portable EXE not found!
    echo.
    echo The EXE file should be at: dist\PC_Hardware_Checker_Professional.exe
    echo.
    echo To create the EXE file, run: BUILD_EXECUTABLE.bat
    echo.
    pause
    exit /b 1
)

echo.
echo This standalone EXE can be copied to any Windows computer
echo and will run without requiring Python installation.
echo.
timeout /t 5 /nobreak >nul
