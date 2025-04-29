#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unlock Page - Interface for unlocking or creating a vault
"""

from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                            QPushButton, QMessageBox, QFrame, QSpacerItem,
                            QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from .base_page import BasePage

class UnlockPage(BasePage):
    """Page for unlocking or creating a vault"""
    
    # Signals
    unlock_successful = pyqtSignal()
    logout_requested = pyqtSignal()
    
    def __init__(self, vault_manager):
        """Initialize the unlock page
        
        Args:
            vault_manager (VaultManager): Vault manager
        """
        super().__init__()
        
        self.vault_manager = vault_manager
        self.username = ""
        self.create_mode = False
        
        # Set up the UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Title
        self.title = self.create_title("Unlock Your Vault")
        self.main_layout.addWidget(self.title)
        
        # Subtitle with username (will be set later)
        self.subtitle = self.create_subtitle("Enter your master password")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.subtitle)
        
        # Unlock form container
        form_container = QFrame()
        form_container.setFrameShape(QFrame.StyledPanel)
        form_container.setMaximumWidth(400)
        form_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)
        
        # Password label
        self.password_label = QLabel("Master Password")
        form_layout.addWidget(self.password_label)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(40)
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password_input)
        
        # Confirm password field (for create mode)
        self.confirm_label = QLabel("Confirm Master Password")
        form_layout.addWidget(self.confirm_label)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setMinimumHeight(40)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.confirm_password_input)
        
        # Hide confirm fields initially (only used in create mode)
        self.confirm_label.setVisible(False)
        self.confirm_password_input.setVisible(False)
        
        # Error message (initially hidden)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)
        
        # Warning message about master password
        self.warning_label = QLabel(
            "Note: Your master password is the key to all your data. "
            "Make sure it's strong and don't forget it. "
            "If you lose your master password, your data cannot be recovered."
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: orange;")
        form_layout.addWidget(self.warning_label)
        
        # Unlock/Create button
        self.action_button = self.create_button("Unlock", self.on_action, True)
        form_layout.addWidget(self.action_button)
        
        # Logout button
        logout_button = self.create_button("Log Out", self.on_logout, False)
        form_layout.addWidget(logout_button)
        
        # Center the form
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(form_container)
        center_layout.addStretch()
        self.main_layout.addLayout(center_layout)
        
        # Add bottom space
        self.main_layout.addStretch()
        
        # Connect enter key in password field to action button
        self.password_input.returnPressed.connect(self.action_button.click)
    
    def set_username(self, username):
        """Set the current username
        
        Args:
            username (str): Current username
        """
        self.username = username
        self.subtitle.setText(f"Welcome back, {username}")
    
    def set_create_mode(self, create=True):
        """Set whether the page is in create or unlock mode
        
        Args:
            create (bool): Whether to use create mode
        """
        self.create_mode = create
        
        if create:
            self.title.setText("Create Your Vault")
            self.subtitle.setText(f"Welcome, {self.username}")
            self.password_label.setText("Create Master Password")
            self.confirm_label.setVisible(True)
            self.confirm_password_input.setVisible(True)
            self.action_button.setText("Create Vault")
        else:
            self.title.setText("Unlock Your Vault")
            self.subtitle.setText(f"Welcome back, {self.username}")
            self.password_label.setText("Master Password")
            self.confirm_label.setVisible(False)
            self.confirm_password_input.setVisible(False)
            self.action_button.setText("Unlock")
    
    def on_action(self):
        """Handle unlock/create button click"""
        password = self.password_input.text()
        
        # Validate inputs
        if not password:
            self.show_message("Master password is required", True)
            return
        
        if self.create_mode:
            # Creating a new vault
            confirm_password = self.confirm_password_input.text()
            
            if password != confirm_password:
                self.show_message("Passwords do not match", True)
                return
            
            if len(password) < 8:
                self.show_message("Master password must be at least 8 characters long", True)
                return
            
            try:
                # Get user_id from username (in a real app, this would be properly handled)
                user_id = self.username  # Simplified for this example
                
                if self.vault_manager.create_vault(user_id, password):
                    self.error_label.setVisible(False)
                    self.clear_fields()
                    self.unlock_successful.emit()
                else:
                    self.show_message("Failed to create vault", True)
            except ValueError as e:
                self.show_message(str(e), True)
        else:
            # Unlocking an existing vault
            try:
                # Get user_id from username (in a real app, this would be properly handled)
                user_id = self.username  # Simplified for this example
                
                if self.vault_manager.unlock_vault(user_id, password):
                    self.error_label.setVisible(False)
                    self.clear_fields()
                    self.unlock_successful.emit()
                else:
                    self.show_message("Invalid master password", True)
            except ValueError as e:
                self.show_message(str(e), True)
    
    def on_logout(self):
        """Handle logout button click"""
        self.clear_fields()
        self.logout_requested.emit()
    
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
        self.password_input.clear()
        self.confirm_password_input.clear()
        self.error_label.setVisible(False) 