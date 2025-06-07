@echo off
echo 🚀 Dealership Microservices Deployment Fixer
echo ==============================================

echo.
echo Your current deployment is missing microservices. This script will help you fix it.
echo.

echo 📋 Current Issues Detected:
echo ❌ Node.js API service not deployed
echo ❌ Sentiment Analysis service not deployed
echo ❌ MongoDB database not connected
echo ❌ Microservices URLs not configured in Django

echo.
echo 🔧 Solutions Available:
echo.
echo 1) 🏗️  Create additional Render services (Recommended)
echo 2) 🚀 Deploy to Railway (All-in-one solution)
echo 3) 🐳 Use Docker on VPS
echo 4) ☁️  Deploy to Google Cloud Run
echo 5) 📖 Show detailed fix instructions

set /p choice="Choose option (1-5): "

if "%choice%"=="1" goto render
if "%choice%"=="2" goto railway
if "%choice%"=="3" goto docker
if "%choice%"=="4" goto gcloud
if "%choice%"=="5" goto guide
goto invalid

:render
echo.
echo 🏗️ Creating Additional Render Services...
echo.
echo Step 1: Set up MongoDB Atlas
echo → Go to https://mongodb.com/atlas
echo → Create free cluster
echo → Get connection string: mongodb+srv://user:pass@cluster.mongodb.net/dealershipsDB
echo.
echo Step 2: Create Node.js API Service
echo → Go to Render Dashboard
echo → New → Web Service
echo → Connect your GitHub repo
echo → Service Name: dealership-nodejs
echo → Environment: Node
echo → Build Command: cd server/database ^&^& npm install
echo → Start Command: cd server/database ^&^& npm start
echo → Add Environment Variable: MONGODB_URL=your-atlas-connection-string
echo.
echo Step 3: Create Sentiment Analysis Service
echo → Go to Render Dashboard
echo → New → Web Service
echo → Service Name: dealership-sentiment
echo → Environment: Python
echo → Build Command: cd server/djangoapp/microservices ^&^& pip install -r requirements.txt
echo → Start Command: cd server/djangoapp/microservices ^&^& python app.py
echo.
echo Step 4: Update Django Service
echo → Add Environment Variables:
echo    backend_url=https://dealership-nodejs.onrender.com
echo    sentiment_analyzer_url=https://dealership-sentiment.onrender.com
goto end

:railway
echo.
echo 🚀 Deploying to Railway...
echo.
where railway >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing Railway CLI...
    npm install -g @railway/cli
)

echo Please login to Railway:
railway login

echo Creating Django service...
cd server
railway init
railway up
cd ..

echo Creating Node.js API service...
cd server\database
railway init
railway up
cd ..\..

echo Creating Sentiment Analysis service...
cd server\djangoapp\microservices
railway init
railway up
cd ..\..\..

echo ✅ Railway deployment complete!
goto end

:docker
echo.
echo 🐳 Docker VPS Deployment...
echo.
echo Step 1: Get a VPS (DigitalOcean, Linode, etc.)
echo Step 2: Install Docker and Docker Compose
echo Step 3: Clone your repository
echo Step 4: Run: docker-compose -f docker-compose.full.yml up -d
echo.
echo Your docker-compose.full.yml is already configured!
goto end

:gcloud
echo.
echo ☁️ Google Cloud Run Deployment...
echo.
echo Step 1: Install Google Cloud SDK
echo Step 2: Authenticate: gcloud auth login
echo Step 3: Set project: gcloud config set project YOUR_PROJECT_ID
echo.
echo Deploy Django:
echo gcloud builds submit --tag gcr.io/PROJECT_ID/dealership-django server/
echo gcloud run deploy --image gcr.io/PROJECT_ID/dealership-django
echo.
echo Deploy Node.js API:
echo gcloud builds submit --tag gcr.io/PROJECT_ID/dealership-nodejs server/database/
echo gcloud run deploy --image gcr.io/PROJECT_ID/dealership-nodejs
echo.
echo Deploy Sentiment Analysis:
echo gcloud builds submit --tag gcr.io/PROJECT_ID/dealership-sentiment server/djangoapp/microservices/
echo gcloud run deploy --image gcr.io/PROJECT_ID/dealership-sentiment
goto end

:guide
echo.
echo 📖 Opening detailed fix instructions...
start DEPLOYMENT-GUIDE.md
goto end

:invalid
echo ❌ Invalid choice. Please run the script again.
goto end

:end
echo.
echo 🎉 Next Steps:
echo 1. Test your API endpoints
echo 2. Import data to MongoDB
echo 3. Update frontend configuration if needed
echo 4. Monitor application logs
echo.
echo 📞 Need help? Check DEPLOYMENT-GUIDE.md for detailed instructions
pause 