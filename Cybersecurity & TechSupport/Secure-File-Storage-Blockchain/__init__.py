import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Import models
from .models import User, File, FileShare, BlockchainEntry

def create_app(test_config=None):
    # Load environment variables
    load_dotenv()
    
    # Create and configure the app
    app = Flask(__name__)
    
    # Configure the app
    if test_config is None:
        # Load the default configuration
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secure-key-for-dev')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secure_storage.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'encrypted_files')
        app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Set up load_user callback for Flask-Login
    @login_manager.user_loader
    def load_user_callback(user_id):
        return User.query.get(int(user_id))
    
    # Import and register blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 