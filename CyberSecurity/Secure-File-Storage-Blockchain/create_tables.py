#!/usr/bin/env python3
"""
Simple database initialization script to create all tables
"""

import os
import sqlite3

def create_tables():
    """Create all necessary database tables directly using SQL"""
    print("Creating database tables...")
    
    # Create or connect to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secure_storage.db')
    
    if os.path.exists(db_path):
        print(f"Database file exists at: {db_path}")
        # Optionally, you can remove it to start fresh
        # os.remove(db_path)
        # print("Removed existing database.")
    
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
    
    # Create sample user for testing (optional)
    # cursor.execute('''
    # INSERT OR IGNORE INTO users (username, email, password_hash, is_active) 
    # VALUES ('test_user', 'test@example.com', 'pbkdf2:sha256:150000$XoLKRd38$739ee5ed650ec9368f05bfb3ef9ab50e677b6cfa1395126ac7fc24b9fd7bc6f7', 1)
    # ''')
    
    # Commit the changes and close the connection
    conn.commit()
    
    # Check if tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Available tables: {', '.join([t[0] for t in tables])}")
    
    conn.close()
    print("Database setup complete!")

if __name__ == "__main__":
    create_tables() 