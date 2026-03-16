# Quick check script that uses the virtual environment Python
# Usage: .\check.ps1

Write-Host "`n[INFO] Running Django system check with virtual environment..." -ForegroundColor Cyan
.\venv\Scripts\python.exe manage.py check
