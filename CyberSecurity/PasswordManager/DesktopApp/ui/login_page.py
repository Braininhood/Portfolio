#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Login Page - User login interface
"""

from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                            QPushButton, QMessageBox, QFrame, QSpacerItem,
                            QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from .base_page import BasePage

class LoginPage(BasePage):
    """Login page for user authentication"""
    
    # Signals
    login_successful = pyqtSignal()
    register_requested = pyqtSignal()
    
    def __init__(self, auth_manager):
        """Initialize the login page
        
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
        title = self.create_title("Secure Vault Password Manager")
        self.main_layout.addWidget(title)
        
        # Login form container
        form_container = QFrame()
        form_container.setFrameShape(QFrame.StyledPanel)
        form_container.setMaximumWidth(400)
        form_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Form title
        login_title = self.create_subtitle("Log In")
        form_layout.addWidget(login_title)
        
        # Username field
        form_layout.addWidget(QLabel("Username"))
        self.username_input = QLineEdit()
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)
        
        # Password field
        form_layout.addWidget(QLabel("Password"))
        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(40)
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password_input)
        
        # Error message (initially hidden)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)
        
        # Login button
        login_button = self.create_button("Log In", self.on_login, True)
        form_layout.addWidget(login_button)
        
        # Register link
        register_layout = QHBoxLayout()
        register_layout.addWidget(QLabel("Don't have an account?"))
        register_button = QPushButton("Register")
        register_button.setFlat(True)
        register_button.setCursor(Qt.PointingHandCursor)
        register_button.clicked.connect(self.on_register)
        register_layout.addWidget(register_button)
        register_layout.addStretch()
        form_layout.addLayout(register_layout)
        
        # Center the form
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_container)
        center_layout.addStretch()
        self.main_layout.addLayout(center_layout)
        
        # Add bottom space
        self.main_layout.addStretch()
        
        # Connect enter key in password field to login
        self.password_input.returnPressed.connect(login_button.click)
    
    def on_login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validate inputs
        if not username:
            self.show_message("Username is required", True)
            return
        
        if not password:
            self.show_message("Password is required", True)
            return
        
        # Check if user exists in the database
        if username not in self.auth_manager.users:
            # User doesn't exist, offer to register
            confirm = QMessageBox.question(
                self, 
                "User Not Found", 
                f"User '{username}' doesn't exist. Would you like to register a new account?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if confirm == QMessageBox.Yes:
                # User wants to register, switch to register page
                self.register_requested.emit()
                
                # Pre-fill username on register page (will be handled by main app)
                self.auth_manager.temp_username = username
                self.auth_manager.temp_password = password
            else:
                self.show_message("Invalid username or password", True)
            
            return
        
        # Try to login
        try:
            if self.auth_manager.login(username, password):
                self.error_label.setVisible(False)
                self.login_successful.emit()
            else:
                # This should not happen as login should raise ValueError on failure
                self.show_message("Invalid username or password", True)
        except ValueError as e:
            # Password incorrect
            self.show_message("Invalid password. Please try again.", True)
    
    def on_register(self):
        """Handle register link click"""
        self.register_requested.emit()
    
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
        self.password_input.clear()
        self.error_label.setVisible(False) 