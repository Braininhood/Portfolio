@echo off
echo 🚀 Starting Full Stack Dealership Application Services
echo ============================================================

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python
    pause
    exit /b 1
)

echo ✅ Dependencies check passed

REM Install npm dependencies for dealer service
echo 📦 Installing npm dependencies for dealer service...
cd database
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install npm dependencies
    pause
    exit /b 1
)
cd ..

REM Install Python dependencies for sentiment service
echo 📦 Installing Python dependencies for sentiment service...
cd djangoapp\microservices
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
cd ..\..

echo ✅ All dependencies installed

REM Start dealer service in background
echo 🚗 Starting dealer service on port 3030...
start "Dealer Service" cmd /k "cd database && node app.js"

REM Wait a moment for dealer service to start
timeout /t 3 /nobreak >nul

REM Start sentiment analyzer service in background
echo 🧠 Starting sentiment analyzer service on port 5050...
start "Sentiment Analyzer" cmd /k "cd djangoapp\microservices && set FLASK_APP=app.py && set FLASK_RUN_PORT=5050 && python -m flask run"

echo.
echo 🎉 Services started successfully!
echo 📊 Service Status:
echo   - Dealer Service: http://localhost:3030
echo   - Sentiment Analyzer: http://localhost:5050
echo.
echo 💡 You can now run Django tests or start the Django server:
echo    Django server: python manage.py runserver
echo    Django tests: python manage.py test
echo.
echo ⏹️  Close the service windows to stop the services
echo.
pause 