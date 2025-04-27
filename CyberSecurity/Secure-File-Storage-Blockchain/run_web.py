from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import sqlite3

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_db_tables():
    """Create all database tables directly using SQLite"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secure_storage.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(100) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(200) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    # Create files table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename VARCHAR(255) NOT NULL,
        encrypted_path VARCHAR(255) NOT NULL UNIQUE,
        encryption_key VARCHAR(255) NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        owner_id INTEGER NOT NULL,
        FOREIGN KEY (owner_id) REFERENCES users (id)
    )
    ''')
    
    # Create file_shares table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS file_shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        shared_with_id INTEGER NOT NULL,
        shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (file_id) REFERENCES files (id),
        FOREIGN KEY (shared_with_id) REFERENCES users (id),
        UNIQUE (file_id, shared_with_id)
    )
    ''')
    
    # Create blockchain table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blockchain (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        file_hash VARCHAR(64) NOT NULL,
        previous_hash VARCHAR(64),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        nonce INTEGER DEFAULT 0,
        FOREIGN KEY (file_id) REFERENCES files (id)
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database tables created using direct SQL.")

def create_app():
    # Create and configure the app
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secure-key-for-testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_storage.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create database tables directly with SQLite before initializing Flask-SQLAlchemy
    create_db_tables()
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    with app.app_context():
        # Import models here to avoid circular imports
        import models
        from routes import main_bp
        
        # Set up load_user callback for Flask-Login using SQLAlchemy 2.0 compatible API
        @login_manager.user_loader
        def load_user(user_id):
            # Use SQLAlchemy 2.0 compatible API: session.get() instead of query.get()
            return db.session.get(models.User, int(user_id))
        
        # Register blueprints
        app.register_blueprint(main_bp)
        
        # Create database tables with SQLAlchemy as well
        db.create_all()
        
        print("Database initialized with SQLAlchemy.")
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("*" * 80)
    print("Secure File Storage Web Interface")
    print("*" * 80)
    print("Access the web interface at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print("*" * 80)
    app.run(debug=True) 