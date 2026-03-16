# Quick runserver script that uses the virtual environment Python
# Usage: .\runserver.ps1

Write-Host "`n[INFO] Starting Django development server with virtual environment..." -ForegroundColor Cyan
.\venv\Scripts\python.exe manage.py runserver
