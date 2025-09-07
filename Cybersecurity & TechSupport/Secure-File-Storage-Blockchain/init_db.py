#!/usr/bin/env python3
"""
Database initialization script for Secure File Storage with Blockchain.
Run this script to create all database tables before starting the application.
"""

import os
import sys
from run_web import create_app, db
from models import User, File, FileShare, BlockchainEntry

def init_db():
    """Initialize the database by creating all tables."""
    app = create_app()
    with app.app_context():
        print("Checking database status...")
        
        # Check if tables exist by trying to query them
        try:
            User.query.first()
            print("Database tables already exist.")
        except Exception as e:
            print(f"Database error: {e}")
            print("Creating database tables...")
            
            # Drop all tables and recreate them
            db.drop_all()
            db.create_all()
            
            print("Database tables created successfully!")
            
            # Optionally create a test user
            # test_user = User(username="test_user", email="test@example.com")
            # test_user.set_password("Password123")
            # db.session.add(test_user)
            # db.session.commit()
            # print("Test user created: test_user / Password123")
        
        # Verify all tables were created
        tables = db.engine.table_names()
        print(f"Available tables: {', '.join(tables)}")

if __name__ == "__main__":
    init_db() 