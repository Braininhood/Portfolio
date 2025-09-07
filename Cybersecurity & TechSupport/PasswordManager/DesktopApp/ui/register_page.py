#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Register Page - User registration interface
"""

from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                            QPushButton, QMessageBox, QFrame, QProgressBar,
                            QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from .base_page import BasePage

class RegisterPage(BasePage):
    """Registration page for new users"""
    
    # Signals
    registration_successful = pyqtSignal()
    login_requested = pyqtSignal()
    
    def __init__(self, auth_manager):
        """Initialize the registration page
        
        Args:
            auth_manager (AuthManager): Authentication manager
        """
        super().__init__()
        
        self.auth_manager = auth_manager
        
        # Set up the UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Title
        title = self.create_title("Create Your Account")
        self.main_layout.addWidget(title)
        
        # Registration form container
        form_container = QFrame()
        form_container.setFrameShape(QFrame.StyledPanel)
        form_container.setMaximumWidth(500)
        form_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Form title
        register_title = self.create_subtitle("Register")
        form_layout.addWidget(register_title)
        
        # Username field
        form_layout.addWidget(QLabel("Username (3-30 characters, letters, numbers, and underscores)"))
        self.username_input = QLineEdit()
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)
        
        # Email field
        form_layout.addWidget(QLabel("Email Address"))
        self.email_input = QLineEdit()
        self.email_input.setMinimumHeight(40)
        form_layout.addWidget(self.email_input)
        
        # Password field
        form_layout.addWidget(QLabel("Password (min 8 characters)"))
        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(40)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.textChanged.connect(self.update_password_strength)
        form_layout.addWidget(self.password_input)
        
        # Password strength indicator
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("Password Strength:"))
        self.strength_progress = QProgressBar()
        self.strength_progress.setMaximum(5)
        self.strength_progress.setTextVisible(False)
        strength_layout.addWidget(self.strength_progress)
        self.strength_label = QLabel("No Password")
        strength_layout.addWidget(self.strength_label)
        form_layout.addLayout(strength_layout)
        
        # Confirm password field
        form_layout.addWidget(QLabel("Confirm Password"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setMinimumHeight(40)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.confirm_password_input)
        
        # Error message (initially hidden)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)
        
        # Register button
        register_button = self.create_button("Register", self.on_register, True)
        form_layout.addWidget(register_button)
        
        # Login link
        login_layout = QHBoxLayout()
        login_layout.addWidget(QLabel("Already have an account?"))
        login_button = QPushButton("Log In")
        login_button.setFlat(True)
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.clicked.connect(self.on_login)
        login_layout.addWidget(login_button)
        login_layout.addStretch()
        form_layout.addLayout(login_layout)
        
        # Center the form
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_container)
        center_layout.addStretch()
        self.main_layout.addLayout(center_layout)
        
        # Add bottom space
        self.main_layout.addStretch()
    
    def update_password_strength(self):
        """Update password strength indicator"""
        password = self.password_input.text()
        
        if not password:
            self.strength_progress.setValue(0)
            self.strength_label.setText("No Password")
            self.strength_progress.setStyleSheet("")
            return
        
        # Use auth manager to check password strength
        strength = self.auth_manager.check_password_strength(password)
        score = strength['score']
        feedback = strength['feedback']
        
        self.strength_progress.setValue(score)
        self.strength_label.setText(feedback)
        
        # Set color based on strength
        if score <= 1:
            self.strength_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif score == 2:
            self.strength_progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        elif score == 3:
            self.strength_progress.setStyleSheet("QProgressBar::chunk { background-color: yellow; }")
        else:
            self.strength_progress.setStyleSheet("QProgressBar::chunk { background-color: green; }")
    
    def on_register(self):
        """Handle register button click"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validate inputs
        if not username or not email or not password:
            self.show_message("All fields are required", True)
            return
        
        if password != confirm_password:
            self.show_message("Passwords do not match", True)
            return
        
        # Check password strength
        strength = self.auth_manager.check_password_strength(password)
        if strength['score'] < 2:
            self.show_message("Please choose a stronger password", True)
            return
        
        # Check if username already exists
        if username in self.auth_manager.users:
            # User already exists, offer to go to login
            confirm = QMessageBox.question(
                self, 
                "User Already Exists", 
                f"User '{username}' already exists. Would you like to log in instead?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if confirm == QMessageBox.Yes:
                # Pre-fill username on login page (will be handled by main app)
                self.auth_manager.temp_username = username
                self.auth_manager.temp_password = password
                
                # Switch to login page
                self.login_requested.emit()
            
            return
        
        # Try to register
        try:
            if self.auth_manager.register(username, email, password):
                self.error_label.setVisible(False)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Registration Successful",
                    "Your account has been created successfully. You can now log in."
                )
                
                # Clear fields
                self.clear_fields()
                
                # Switch to login page with credentials pre-filled
                self.auth_manager.temp_username = username
                self.auth_manager.temp_password = password
                self.login_requested.emit()
        except ValueError as e:
            self.show_message(str(e), True)
    
    def on_login(self):
        """Handle login link click"""
        self.login_requested.emit()
    
    def show_message(self, message, error=False):
        """Show a message to the user
        
        Args:
            message (str): Message to show
            error (bool, optional): Whether this is an error message
        """
        if error:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
        else:
            self.error_label.setVisible(False)
            QMessageBox.information(self, "Information", message)
    
    def clear_fields(self):
        """Clear all input fields"""
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.error_label.setVisible(False)
        self.strength_progress.setValue(0)
        self.strength_label.setText("No Password")
        
    def populate_from_temp_data(self):
        """Populate fields from temporary data
        
        This is used when redirected from login page to pre-fill the form
        """
        if hasattr(self.auth_manager, 'temp_username'):
            self.username_input.setText(self.auth_manager.temp_username)
            
        if hasattr(self.auth_manager, 'temp_password'):
            self.password_input.setText(self.auth_manager.temp_password)
            self.confirm_password_input.setText(self.auth_manager.temp_password)
            self.update_password_strength() 