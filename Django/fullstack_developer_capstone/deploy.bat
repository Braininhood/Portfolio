@echo off
echo 🚀 Dealership Application Deployment Script
echo ===========================================

echo.
echo Choose deployment option:
echo 1) Railway (Recommended - Easy setup)
echo 2) Render (Full-stack friendly)
echo 3) Fly.io (Global edge deployment)
echo 4) Build Docker images locally
echo 5) Show deployment guide

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto railway
if "%choice%"=="2" goto render
if "%choice%"=="3" goto fly
if "%choice%"=="4" goto build_local
if "%choice%"=="5" goto show_guide
goto invalid

:railway
echo 📡 Deploying to Railway...
echo Installing Railway CLI...
npm install -g @railway/cli
echo Please login to Railway:
railway login
echo Initializing Railway project...
railway init
echo Deploying to Railway...
railway up
echo ✅ Railway deployment complete!
echo 🌐 Your app will be available at the URL provided by Railway
goto end

:render
echo 🎨 Deploying to Render...
echo Please follow these steps:
echo 1. Go to https://render.com
echo 2. Connect your GitHub repository
echo 3. Use the render.yaml file in your repo root
echo 4. Render will automatically deploy all services
echo ✅ Render deployment setup complete!
goto end

:fly
echo 🪰 Deploying to Fly.io...
echo Installing Fly CLI...
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
echo Please login to Fly.io:
fly auth login
echo Launching Fly.io app...
fly launch --dockerfile server/Dockerfile.prod
echo ✅ Fly.io deployment complete!
goto end

:build_local
echo 🐳 Building Docker images locally...
echo Building React frontend...
cd server\frontend
docker build -f Dockerfile.prod -t dealership-frontend .
cd ..\..
echo Building Django backend...
cd server
docker build -f Dockerfile.prod -t dealership-backend .
cd ..
echo Building Node.js API...
cd server\database
docker build -f Dockerfile.prod -t dealership-nodejs-api .
cd ..\..
echo ✅ All Docker images built successfully!
echo 🚀 You can now push these images to any container registry
goto end

:show_guide
echo 📖 Opening deployment guide...
type DEPLOYMENT-OPTIONS.md
goto end

:invalid
echo ❌ Invalid choice. Please run the script again.
goto end

:end
echo.
echo 🎉 Deployment process completed!
echo 📚 Check DEPLOYMENT-OPTIONS.md for more detailed instructions
pause 