@echo off
REM Kill processes on ports 8080 and 8081. Run: scripts\kill-ports.cmd
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8081') do taskkill /F /PID %%a 2>nul
echo Done.
