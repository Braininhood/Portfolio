#!/usr/bin/env python3
"""
Startup script for all microservices required by the Django backend.
This script starts:
1. Dealer service (Node.js on port 3030)
2. Sentiment analyzer service (Flask on port 5050)
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

# Get the server directory
SERVER_DIR = Path(__file__).parent
DATABASE_DIR = SERVER_DIR / "database"
MICROSERVICES_DIR = SERVER_DIR / "djangoapp" / "microservices"

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_dealer_service(self):
        """Start the Node.js dealer service on port 3030"""
        print("🚗 Starting dealer service on port 3030...")
        try:
            # Change to database directory and start the service
            process = subprocess.Popen(
                ["node", "app.js"],
                cwd=DATABASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(("Dealer Service", process))
            print("✅ Dealer service started successfully")
            return process
        except Exception as e:
            print(f"❌ Failed to start dealer service: {e}")
            return None
    
    def start_sentiment_service(self):
        """Start the Flask sentiment analyzer service on port 5050"""
        print("🧠 Starting sentiment analyzer service on port 5050...")
        try:
            # Install required packages first
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], cwd=MICROSERVICES_DIR, check=True)
            
            # Download NLTK data
            import nltk
            try:
                nltk.data.find('vader_lexicon')
            except LookupError:
                print("📥 Downloading NLTK VADER lexicon...")
                nltk.download('vader_lexicon')
            
            # Start the Flask service
            env = os.environ.copy()
            env["FLASK_APP"] = "app.py"
            env["FLASK_RUN_PORT"] = "5050"
            env["FLASK_RUN_HOST"] = "0.0.0.0"
            
            process = subprocess.Popen(
                [sys.executable, "-m", "flask", "run"],
                cwd=MICROSERVICES_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(("Sentiment Service", process))
            print("✅ Sentiment analyzer service started successfully")
            return process
        except Exception as e:
            print(f"❌ Failed to start sentiment service: {e}")
            return None
    
    def check_services(self):
        """Check if services are running and restart if needed"""
        while self.running:
            for name, process in self.processes[:]:
                if process.poll() is not None:
                    print(f"⚠️  {name} stopped unexpectedly")
                    self.processes.remove((name, process))
                    if name == "Dealer Service":
                        self.start_dealer_service()
                    elif name == "Sentiment Service":
                        self.start_sentiment_service()
            time.sleep(5)
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        self.running = False
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 {name} force killed")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n📡 Received signal {signum}")
        self.stop_all_services()
        sys.exit(0)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found. Please install Node.js")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js")
        return False
    
    # Check Python
    print(f"✅ Python: {sys.version}")
    
    # Check if database directory exists
    if not DATABASE_DIR.exists():
        print(f"❌ Database directory not found: {DATABASE_DIR}")
        return False
    
    # Check if microservices directory exists
    if not MICROSERVICES_DIR.exists():
        print(f"❌ Microservices directory not found: {MICROSERVICES_DIR}")
        return False
    
    return True

def install_npm_dependencies():
    """Install npm dependencies for the dealer service"""
    print("📦 Installing npm dependencies for dealer service...")
    try:
        subprocess.run(["npm", "install"], cwd=DATABASE_DIR, check=True)
        print("✅ npm dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install npm dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js and npm")
        return False

def main():
    """Main function to start all services"""
    print("🚀 Starting Full Stack Dealership Application Services")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)
    
    # Install npm dependencies
    if not install_npm_dependencies():
        print("❌ Failed to install npm dependencies.")
        sys.exit(1)
    
    # Create service manager
    manager = ServiceManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        # Start services
        dealer_process = manager.start_dealer_service()
        sentiment_process = manager.start_sentiment_service()
        
        if not dealer_process and not sentiment_process:
            print("❌ Failed to start any services")
            sys.exit(1)
        
        print("\n🎉 Services started successfully!")
        print("📊 Service Status:")
        print("  - Dealer Service: http://localhost:3030")
        print("  - Sentiment Analyzer: http://localhost:5050")
        print("\n💡 You can now run Django tests or start the Django server")
        print("   Django server: python manage.py runserver")
        print("   Django tests: python manage.py test")
        print("\n⏹️  Press Ctrl+C to stop all services")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=manager.check_services, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        while manager.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        manager.stop_all_services()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        manager.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main() 