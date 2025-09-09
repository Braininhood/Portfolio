#!/usr/bin/env python3
"""
Data Automation Setup Script
Automated setup for the Data Automation web application
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Current version:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_node_version():
    """Check if Node.js is installed"""
    print("📦 Checking Node.js...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node.js is not installed. Please install Node.js 16+ from https://nodejs.org/")
    return False

def setup_backend():
    """Setup Django backend"""
    print("\n🚀 Setting up Django backend...")
    
    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    # Activate virtual environment and install dependencies
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Run Django migrations
    if not run_command(f"{python_cmd} manage.py makemigrations", "Creating Django migrations"):
        return False
    
    if not run_command(f"{python_cmd} manage.py migrate", "Applying Django migrations"):
        return False
    
    print("✅ Backend setup completed successfully")
    return True

def setup_frontend():
    """Setup React frontend"""
    print("\n⚛️ Setting up React frontend...")
    
    # Change to frontend directory
    if not os.path.exists("frontend"):
        print("❌ Frontend directory not found")
        return False
    
    os.chdir("frontend")
    
    # Install dependencies
    if not run_command("npm install", "Installing Node.js dependencies"):
        return False
    
    # Go back to root directory
    os.chdir("..")
    
    print("✅ Frontend setup completed successfully")
    return True

def create_env_file():
    """Create .env file with default values"""
    print("\n⚙️ Creating environment configuration...")
    
    env_content = """# Django Settings
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Email Settings (configure these for email functionality)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery Settings (optional, for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Frontend Settings
REACT_APP_API_URL=http://localhost:8000/api
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
        print("⚠️  Please update the .env file with your actual settings")
    else:
        print("✅ .env file already exists")
    
    return True

def main():
    """Main setup function"""
    print("🎯 Data Automation Setup Script")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_node_version():
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("❌ Environment configuration failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your actual settings")
    print("2. Start the backend server: python manage.py runserver")
    print("3. Start the frontend server: cd frontend && npm start")
    print("4. Open http://localhost:3000 in your browser")
    print("\n📚 For detailed instructions, see README.md")

if __name__ == "__main__":
    main()