@echo off
title PC Hardware Checker Professional - Quick Start
echo ================================================================
echo           PC Hardware Checker Professional
echo ================================================================
echo.
echo Welcome! This is the quick start launcher.
echo.
echo INSTALLATION OPTIONS:
echo [1] Basic Features Only        (launchers\INSTALL_BASIC.bat)
echo [2] Minimal Stress Testing     (launchers\install_stress_simple.bat) 
echo [3] Professional Features      (launchers\INSTALL_PROFESSIONAL.bat)
echo [4] Complete Installation      (launchers\install.bat)
echo.
echo QUICK START:
echo [R] Run Application            (launchers\RUN_AS_ADMIN.bat)
echo [P] Run Portable Version       (QUICK_START_PORTABLE.bat)
echo [H] Help Documentation         (docs\README.md)
echo.
echo Choose an option (1-4, R, P, H) or press any key to continue...
set /p choice=Enter choice: 

if /i "%choice%"=="1" (
    echo Starting basic installation...
    start launchers\INSTALL_BASIC.bat
) else if /i "%choice%"=="2" (
    echo Starting minimal stress testing installation...
    start launchers\install_stress_simple.bat
) else if /i "%choice%"=="3" (
    echo Starting professional installation...
    start launchers\INSTALL_PROFESSIONAL.bat
) else if /i "%choice%"=="4" (
    echo Starting complete installation...
    start launchers\install.bat
) else if /i "%choice%"=="R" (
    echo Starting application with admin privileges...
    start launchers\RUN_AS_ADMIN.bat
) else if /i "%choice%"=="P" (
    echo Starting portable version...
    start QUICK_START_PORTABLE.bat
) else if /i "%choice%"=="H" (
    echo Opening documentation...
    start docs\README.md
) else (
    echo Invalid choice. Opening documentation...
    start docs\README.md
)

echo.
echo Done! Check the opened windows for progress.
pause
