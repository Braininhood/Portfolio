import re
from flask import session
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from . import db
from .models import User
from .crypto import derive_key_from_password

# Initialize password hasher with Argon2
ph = PasswordHasher(
    time_cost=3,       # Number of iterations
    memory_cost=65536, # Memory usage (64 MB)
    parallelism=4,     # Degree of parallelism
    hash_len=32,       # Hash output length
    salt_len=16        # Salt length
)

def load_user(user_id):
    """Load a user from the database by ID for Flask-Login"""
    return User.query.get(int(user_id))

def validate_password_strength(password):
    """
    Validate that a password meets minimum security requirements
    Returns (is_valid, message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    # Check for at least one uppercase letter, lowercase letter, digit, and special character
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Common password check would be more robust with a dictionary
    common_passwords = ["password123", "123456789", "qwerty123", "admin123"]
    if password.lower() in common_passwords:
        return False, "Password is too common and easily guessable"
    
    return True, "Password meets requirements"

def register_user(username, email, password):
    """
    Register a new user with validation
    Returns True if successful, False if registration failed
    """
    # Check if username or email already exists
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return False
    
    # Validate password strength
    is_valid, _ = validate_password_strength(password)
    if not is_valid:
        return False
    
    # Hash the password with Argon2
    password_hash = ph.hash(password)
    
    # Create a new user
    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )
    
    # Add to database
    db.session.add(new_user)
    db.session.commit()
    
    return True

def authenticate_user(email, password):
    """
    Authenticate a user by email and password
    Returns the User object if authentication is successful, None otherwise
    """
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return None
    
    try:
        # Verify the password hash with Argon2
        ph.verify(user.password_hash, password)
        
        # Check if the hash needs to be updated (e.g., if parameters changed)
        if ph.check_needs_rehash(user.password_hash):
            user.password_hash = ph.hash(password)
            db.session.commit()
        
        return user
    except VerifyMismatchError:
        # Password verification failed
        return None

def change_password(user_id, current_password, new_password):
    """
    Change a user's password with verification
    Returns (success, message)
    """
    user = User.query.get(user_id)
    
    if not user:
        return False, "User not found"
    
    try:
        # Verify the current password
        ph.verify(user.password_hash, current_password)
        
        # Validate the new password
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return False, message
        
        # Hash and store the new password
        user.password_hash = ph.hash(new_password)
        db.session.commit()
        
        return True, "Password changed successfully"
    except VerifyMismatchError:
        return False, "Current password is incorrect"

def get_user_encryption_key(user_id, password):
    """
    Derive a consistent encryption key from a user's password
    Used for encrypting file keys
    """
    user = User.query.get(user_id)
    
    if not user:
        return None
    
    # Use email as salt (consistent for each user)
    salt = user.email.encode()
    
    # Derive key
    key, _ = derive_key_from_password(password, salt)
    
    return key 