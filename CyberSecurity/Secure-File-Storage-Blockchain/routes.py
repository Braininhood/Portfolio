import os
import hashlib
import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from run_web import db
from models import User, File, FileShare, BlockchainEntry
from crypto import Crypto
from blockchain import Blockchain
from file_manager import FileManager

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Helper functions that might have been in utils.py
def encrypt_file(file_obj, output_path):
    """
    Encrypt a file using AES-256-CBC
    Returns the encryption key
    """
    # Save to temporary file first
    temp_path = os.path.join(os.path.dirname(output_path), "temp_" + os.path.basename(output_path))
    file_obj.save(temp_path)
    
    # Generate a random password for file encryption
    import secrets
    password = secrets.token_hex(16)
    
    # Encrypt the file
    Crypto.encrypt_file(temp_path, password, output_path)
    
    # Remove temp file
    os.remove(temp_path)
    
    return password

def decrypt_file(encrypted_path, key, output_path):
    """
    Decrypt a file using AES-256-CBC
    """
    result, success = Crypto.decrypt_file(encrypted_path, key, output_path)
    return result

def verify_blockchain_integrity():
    """
    Verify the integrity of the entire blockchain
    """
    blockchain = Blockchain()
    return blockchain.verify_chain_integrity()

# Input validation helpers
def validate_username(username):
    """Validate username - letters, numbers, underscores, 3-20 chars"""
    import re
    if not username or not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return False
    return True

def validate_password(password):
    """Validate password - at least 8 chars, 1 uppercase, 1 lowercase, 1 number"""
    import re
    if not password or len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def validate_email(email):
    """Validate email format"""
    import re
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False
    return True

# Authentication routes
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Validate inputs
        if not validate_username(username):
            flash('Username must be 3-20 characters and contain only letters, numbers, and underscores', 'danger')
            return redirect(url_for('main.register'))
        
        if not validate_password(password):
            flash('Password must be at least 8 characters with at least one uppercase letter, one lowercase letter, and one number', 'danger')
            return redirect(url_for('main.register'))
            
        if not validate_email(email):
            flash('Please enter a valid email address', 'danger')
            return redirect(url_for('main.register'))
        
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists. Please login instead.', 'warning')
            return redirect(url_for('main.login'))
        
        # Check if email already exists
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('Email already registered. Please login instead.', 'warning')
            return redirect(url_for('main.login'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate inputs
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return redirect(url_for('main.login'))
        
        # Use SQLAlchemy 2.0 compatible query pattern
        stmt = db.select(User).filter_by(username=username)
        user = db.session.execute(stmt).scalar_one_or_none()
        
        if not user:
            flash('User does not exist. Please register first.', 'warning')
            return redirect(url_for('main.register'))
        
        if not check_password_hash(user.password_hash, password):
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('main.login'))
        
        login_user(user)
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# Main application routes
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    files = File.query.filter_by(owner_id=current_user.id).all()
    shared_files = FileShare.query.filter_by(shared_with_id=current_user.id).all()
    return render_template('dashboard.html', files=files, shared_files=shared_files)

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Validate file size (client-side validation is also in the template)
        if request.content_length > current_app.config['MAX_CONTENT_LENGTH']:
            flash(f'File too large. Maximum size is {current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)}MB', 'danger')
            return redirect(request.url)
            
        # Validate file type if needed
        # allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
        # if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        #     flash('File type not allowed', 'danger')
        #     return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            
            # Generate a unique file identifier
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            file_id = f"{current_user.id}_{timestamp}_{filename}"
            
            # Calculate original file hash for blockchain
            file_content = file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            file.seek(0)  # Reset file pointer
            
            # Encrypt and save the file
            encrypted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_id)
            encryption_key = encrypt_file(file, encrypted_path)
            
            # Store file info in database
            new_file = File(
                filename=filename,
                encrypted_path=encrypted_path,
                encryption_key=encryption_key,
                owner_id=current_user.id
            )
            db.session.add(new_file)
            db.session.commit()
            
            # Add file to blockchain
            new_entry = BlockchainEntry(
                file_id=new_file.id,
                file_hash=file_hash,
                timestamp=datetime.datetime.now()
            )
            db.session.add(new_entry)
            db.session.commit()
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('main.dashboard'))
    
    return render_template('upload.html')

@main_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # Check if user is the owner or has shared access
    if file.owner_id != current_user.id:
        shared = FileShare.query.filter_by(
            file_id=file_id,
            shared_with_id=current_user.id
        ).first()
        
        if not shared:
            flash('Access denied', 'danger')
            return redirect(url_for('main.dashboard'))
    
    # Decrypt the file to a temporary location
    temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{file.filename}")
    decrypt_file(file.encrypted_path, file.encryption_key, temp_path)
    
    # Verify blockchain integrity
    blockchain_entry = BlockchainEntry.query.filter_by(file_id=file.id).order_by(BlockchainEntry.timestamp.desc()).first()
    
    is_valid = verify_blockchain_integrity()
    if not is_valid:
        flash('Warning: File integrity check failed. The file may have been tampered with.', 'danger')
    
    # Return the file and remove temp file
    return_value = send_file(temp_path, as_attachment=True, download_name=file.filename)
    
    # Clean up temp file (in a production environment, this would need more robust handling)
    # os.remove(temp_path)  # Uncomment for production
    
    return return_value

@main_bp.route('/share/<int:file_id>', methods=['GET', 'POST'])
@login_required
def share_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # Check if user is the owner
    if file.owner_id != current_user.id:
        flash('You do not have permission to share this file', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        
        if not username:
            flash('Please enter a username', 'danger')
            return redirect(url_for('main.share_file', file_id=file_id))
            
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('main.share_file', file_id=file_id))
            
        # Prevent sharing with yourself
        if user.id == current_user.id:
            flash('You cannot share a file with yourself', 'warning')
            return redirect(url_for('main.share_file', file_id=file_id))
        
        # Check if already shared
        existing_share = FileShare.query.filter_by(
            file_id=file_id,
            shared_with_id=user.id
        ).first()
        
        if existing_share:
            flash('File already shared with this user', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Create new share
        new_share = FileShare(
            file_id=file_id,
            shared_with_id=user.id
        )
        db.session.add(new_share)
        db.session.commit()
        
        flash(f'File shared with {username}', 'success')
        return redirect(url_for('main.dashboard'))
    
    # For the GET request, fetch all users the file is shared with
    shares = FileShare.query.filter_by(file_id=file_id).all()
    # For each share, fetch the associated user
    for share in shares:
        share.shared_user = User.query.get(share.shared_with_id)
    
    # Attach shares to the file object for the template
    file.shares = shares
    
    return render_template('share.html', file=file)

@main_bp.route('/verify/<int:file_id>')
@login_required
def verify_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # Check if user is the owner or has shared access
    if file.owner_id != current_user.id:
        shared = FileShare.query.filter_by(
            file_id=file_id,
            shared_with_id=current_user.id
        ).first()
        
        if not shared:
            flash('Access denied', 'danger')
            return redirect(url_for('main.dashboard'))
    
    # Get blockchain entries for this file
    blockchain_entries = BlockchainEntry.query.filter_by(file_id=file.id).order_by(BlockchainEntry.timestamp).all()
    
    return render_template('verify.html', file=file, blockchain_entries=blockchain_entries)

@main_bp.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('500.html'), 500 