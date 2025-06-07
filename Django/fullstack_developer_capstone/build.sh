#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # exit on error

echo "🚀 Starting Render build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd server
pip install -r requirements.txt

# Build React frontend
echo "⚛️ Building React frontend..."
cd frontend
npm ci --only=production
npm run build

# Go back to server directory
cd ..

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --settings=djangoproj.production_settings

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --settings=djangoproj.production_settings

# Populate database with sample data
echo "🚗 Populating database with sample data..."
python manage.py populate_db --settings=djangoproj.production_settings

echo "✅ Build completed successfully!" 