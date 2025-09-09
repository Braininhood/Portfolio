@echo off
echo Starting Django backend...
call venv\Scripts\activate
python manage.py runserver
pause
