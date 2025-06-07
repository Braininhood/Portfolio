#!/bin/bash

echo "🚀 Dealership Application Deployment Script"
echo "==========================================="

# Function to deploy to Railway
deploy_railway() {
    echo "📡 Deploying to Railway..."
    
    # Check if Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    # Login and deploy
    echo "Please login to Railway:"
    railway login
    
    echo "Initializing Railway project..."
    railway init
    
    echo "Deploying to Railway..."
    railway up
    
    echo "✅ Railway deployment complete!"
    echo "🌐 Your app will be available at the URL provided by Railway"
}

# Function to deploy to Render
deploy_render() {
    echo "🎨 Deploying to Render..."
    echo "Please follow these steps:"
    echo "1. Go to https://render.com"
    echo "2. Connect your GitHub repository"
    echo "3. Use the render.yaml file in your repo root"
    echo "4. Render will automatically deploy all services"
    echo "✅ Render deployment setup complete!"
}

# Function to deploy to Fly.io
deploy_fly() {
    echo "🪰 Deploying to Fly.io..."
    
    # Check if Fly CLI is installed
    if ! command -v fly &> /dev/null; then
        echo "Installing Fly CLI..."
        curl -L https://fly.io/install.sh | sh
    fi
    
    # Login and deploy
    echo "Please login to Fly.io:"
    fly auth login
    
    echo "Launching Fly.io app..."
    fly launch --dockerfile server/Dockerfile.prod
    
    echo "✅ Fly.io deployment complete!"
}

# Function to build Docker images locally
build_local() {
    echo "🐳 Building Docker images locally..."
    
    # Build frontend
    echo "Building React frontend..."
    cd server/frontend
    docker build -f Dockerfile.prod -t dealership-frontend .
    cd ../..
    
    # Build backend
    echo "Building Django backend..."
    cd server
    docker build -f Dockerfile.prod -t dealership-backend .
    cd ..
    
    # Build Node.js API
    echo "Building Node.js API..."
    cd server/database
    docker build -f Dockerfile.prod -t dealership-nodejs-api .
    cd ../..
    
    echo "✅ All Docker images built successfully!"
    echo "🚀 You can now push these images to any container registry"
}

# Main menu
echo ""
echo "Choose deployment option:"
echo "1) Railway (Recommended - Easy setup)"
echo "2) Render (Full-stack friendly)"
echo "3) Fly.io (Global edge deployment)"
echo "4) Build Docker images locally"
echo "5) Show deployment guide"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        deploy_railway
        ;;
    2)
        deploy_render
        ;;
    3)
        deploy_fly
        ;;
    4)
        build_local
        ;;
    5)
        echo "📖 Opening deployment guide..."
        if command -v code &> /dev/null; then
            code DEPLOYMENT-OPTIONS.md
        else
            cat DEPLOYMENT-OPTIONS.md
        fi
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment process completed!"
echo "📚 Check DEPLOYMENT-OPTIONS.md for more detailed instructions" 