from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from run_web import db

class User(UserMixin, db.Model):
    """User model for authentication and account management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    files = db.relationship('File', backref='owner', lazy=True)
    shared_with_me = db.relationship('FileShare', backref='shared_user', lazy=True, 
                                     foreign_keys='FileShare.shared_with_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # Required for Flask-Login
    def get_id(self):
        return str(self.id)

class File(db.Model):
    """File model to store file metadata"""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    encrypted_path = db.Column(db.String(255), unique=True, nullable=False)
    encryption_key = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    blockchain_entries = db.relationship('BlockchainEntry', backref='file', lazy=True)
    shares = db.relationship('FileShare', backref='file', lazy=True)
    
    def __repr__(self):
        return f'<File {self.filename}>'

class FileShare(db.Model):
    """Model for file sharing between users"""
    __tablename__ = 'file_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('file_id', 'shared_with_id', name='unique_file_share'),
    )
    
    def __repr__(self):
        return f'<FileShare file_id={self.file_id} shared_with={self.shared_with_id}>'

class BlockchainEntry(db.Model):
    """Model for blockchain entries"""
    __tablename__ = 'blockchain'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)  # SHA-256 hash (32 bytes = 64 hex chars)
    previous_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash of previous entry
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    nonce = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<BlockchainEntry id={self.id} file_id={self.file_id}>'
    
    @classmethod
    def get_latest_hash(cls):
        """Get the hash of the last block in the chain"""
        latest_block = cls.query.order_by(cls.id.desc()).first()
        return latest_block.file_hash if latest_block else None 