@echo off
echo Starting Data Automation Web Application...
echo.

echo Starting Django backend...
start "Django Backend" cmd /k "venv\Scripts\activate && python manage.py runserver"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak > nul

echo Starting React frontend...
start "React Frontend" cmd /k "cd frontend && npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause > nul
