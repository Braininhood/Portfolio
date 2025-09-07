#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auth Manager - Handles user authentication and management.
"""

import os
import json
import hashlib
import uuid
import re

class AuthManager:
    """Manages user authentication and user data"""
    
    def __init__(self):
        """Initialize the auth manager"""
        self.current_user = None
        self.users = {}
        self.app_data_dir = os.path.join(os.path.expanduser('~'), '.secure_vault')
        self.users_file = os.path.join(self.app_data_dir, 'users.json')
        
        # Temporary storage for transferring data between pages
        self.temp_username = None
        self.temp_password = None
        
        # Create app data directory if it doesn't exist
        if not os.path.exists(self.app_data_dir):
            try:
                os.makedirs(self.app_data_dir)
                print(f"Created application directory: {self.app_data_dir}")
            except Exception as e:
                print(f"Error creating application directory: {e}")
        
        # Load users from file
        self.load_users()
        
        # Initialize DB if empty
        if not self.users:
            print("No users found. Database will be created when the first user registers.")
    
    def load_users(self):
        """Load users from the users file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
                print(f"Loaded {len(self.users)} users from database")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading users: {e}")
                self.users = {}
        else:
            print(f"Users file not found: {self.users_file}")
            self.users = {}
    
    def save_users(self):
        """Save users to the users file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            print(f"Saved {len(self.users)} users to database")
            return True
        except IOError as e:
            print(f"Error saving users: {e}")
            return False
    
    def register(self, username, email, password):
        """Register a new user
        
        Args:
            username (str): Username
            email (str): Email address
            password (str): Password
            
        Returns:
            bool: True if registration was successful
            
        Raises:
            ValueError: If username already exists or validation fails
        """
        # Validate inputs
        if not username or not email or not password:
            raise ValueError("Username, email, and password are required")
        
        # Check if username already exists
        if username in self.users:
            raise ValueError("Username already exists")
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            raise ValueError("Username must be 3-30 characters and contain only letters, numbers, and underscores")
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email address")
        
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Hash password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Create user
        user = {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'created': self._get_timestamp()
        }
        
        # Save user
        self.users[username] = user
        
        # Save to file
        if not self.save_users():
            raise ValueError("Failed to save user to database")
        
        # Set current user
        self.current_user = {
            'id': user_id,
            'username': username,
            'email': email
        }
        
        return True
    
    def login(self, username, password):
        """Login a user
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            bool: True if login was successful
            
        Raises:
            ValueError: If login fails
        """
        # Check if username exists
        if username not in self.users:
            raise ValueError("Invalid username or password")
        
        # Get user
        user = self.users[username]
        
        # Verify password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if user['password_hash'] != password_hash:
            raise ValueError("Invalid username or password")
        
        # Set current user
        self.current_user = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
        
        # Clear temporary data
        self.temp_username = None
        self.temp_password = None
        
        return True
    
    def logout(self):
        """Logout the current user"""
        self.current_user = None
        
        # Clear temporary data
        self.temp_username = None
        self.temp_password = None
    
    def is_authenticated(self):
        """Check if a user is currently authenticated
        
        Returns:
            bool: True if authenticated
        """
        return self.current_user is not None
    
    def get_current_user(self):
        """Get the current authenticated user
        
        Returns:
            dict: Current user data or None if not authenticated
        """
        return self.current_user
    
    def user_exists(self, username):
        """Check if a user exists
        
        Args:
            username (str): Username to check
            
        Returns:
            bool: True if the user exists
        """
        return username in self.users
    
    def check_password_strength(self, password):
        """Check the strength of a password
        
        Args:
            password (str): Password to check
            
        Returns:
            dict: Strength assessment with score and feedback
        """
        if not password:
            return {'score': 0, 'feedback': 'Very Weak'}
        
        score = 0
        
        # Length
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        
        # Complexity
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[0-9]', password):
            score += 1
        if re.search(r'[^A-Za-z0-9]', password):
            score += 1
        
        # Cap score at 5
        score = min(score, 5)
        
        # Feedback based on score
        if score >= 4:
            feedback = 'Strong'
        elif score >= 3:
            feedback = 'Good'
        elif score >= 2:
            feedback = 'Fair'
        elif score >= 1:
            feedback = 'Weak'
        else:
            feedback = 'Very Weak'
        
        return {'score': score, 'feedback': feedback}
    
    def delete_user(self, username, password=None):
        """Delete a user and their data
        
        Args:
            username (str): Username to delete
            password (str, optional): If provided, verify password before deletion
            
        Returns:
            bool: True if user was deleted successfully
            
        Raises:
            ValueError: If user doesn't exist or password is incorrect
        """
        # Check if user exists
        if username not in self.users:
            raise ValueError(f"User '{username}' does not exist")
        
        # Verify password if provided
        if password is not None:
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if self.users[username]['password_hash'] != password_hash:
                raise ValueError("Incorrect password")
        
        # Delete user
        user_data = self.users.pop(username)
        
        # Save changes
        if not self.save_users():
            # Restore user if save fails
            self.users[username] = user_data
            raise ValueError("Failed to save changes after user deletion")
        
        # If the deleted user was the current user, log out
        if self.current_user and self.current_user['username'] == username:
            self.logout()
        
        return True
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.utcnow().isoformat()