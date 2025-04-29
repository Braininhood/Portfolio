#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Secure Vault Password Manager - Main Application
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QStackedWidget, 
                            QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QGridLayout, QMessageBox, QDesktopWidget,
                            QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

# Import modules with try/except to handle missing files gracefully
try:
    from auth_manager import AuthManager
    from vault_manager import VaultManager
    from crypto_service import CryptoService
    from password_generator import PasswordGenerator

    # Import UI components
    try:
        from ui import LoginPage, RegisterPage, UnlockPage, VaultPage
        UI_AVAILABLE = True
    except ImportError as e:
        print(f"Error importing UI components: {e}")
        UI_AVAILABLE = False
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)

class PasswordManagerApp(QMainWindow):
    """Main application window for the password manager"""
    
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Secure Vault Password Manager")
        self.setMinimumSize(900, 700)
        
        # Initialize managers
        try:
            self.crypto_service = CryptoService()
            self.auth_manager = AuthManager()
            self.vault_manager = VaultManager(self.crypto_service)
            self.password_generator = PasswordGenerator()
            
            # Track the current master password
            self.current_master_password = None
        except Exception as e:
            self.show_error_and_exit(f"Failed to initialize core services: {str(e)}")
        
        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create stacked widget for page navigation
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Check if UI components are available
        if not UI_AVAILABLE:
            self.show_error_and_exit("UI components are not available. Please make sure the 'ui' directory exists.")
        
        # Initialize pages
        try:
            self.init_pages()
        except Exception as e:
            self.show_error_and_exit(f"Failed to initialize UI pages: {str(e)}")
        
        # Center the window
        self.center()
    
    def show_error_and_exit(self, message):
        """Show error message and exit application
        
        Args:
            message (str): Error message
        """
        print(f"Critical error: {message}")
        QMessageBox.critical(self, "Critical Error", message)
        sys.exit(1)
        
    def init_pages(self):
        """Initialize all application pages"""
        try:
            # Create pages
            self.login_page = LoginPage(self.auth_manager)
            self.register_page = RegisterPage(self.auth_manager)
            self.unlock_page = UnlockPage(self.vault_manager)
            self.vault_page = VaultPage(self.vault_manager, self.password_generator)
            
            # Add pages to stacked widget
            self.stacked_widget.addWidget(self.login_page)
            self.stacked_widget.addWidget(self.register_page)
            self.stacked_widget.addWidget(self.unlock_page)
            self.stacked_widget.addWidget(self.vault_page)
            
            # Connect page signals
            self.login_page.register_requested.connect(self.show_register_page)
            self.login_page.login_successful.connect(self.on_login_successful)
            
            self.register_page.login_requested.connect(self.show_login_page)
            # Note: We're no longer using registration_successful signal
            # as we're redirecting to login page directly after registration
            
            self.unlock_page.logout_requested.connect(self.logout)
            self.unlock_page.unlock_successful.connect(self.on_unlock_successful)
            
            self.vault_page.lock_requested.connect(self.lock_vault)
            self.vault_page.logout_requested.connect(self.logout)
            
            # Show login page by default
            self.show_login_page()
        except Exception as e:
            print(f"Error initializing pages: {e}")
            traceback.print_exc()
            raise
    
    def show_login_page(self):
        """Switch to login page"""
        self.stacked_widget.setCurrentWidget(self.login_page)
        
        # Populate fields from temporary data if available
        if hasattr(self.auth_manager, 'temp_username') and self.auth_manager.temp_username:
            self.login_page.username_input.setText(self.auth_manager.temp_username)
            
            if hasattr(self.auth_manager, 'temp_password') and self.auth_manager.temp_password:
                self.login_page.password_input.setText(self.auth_manager.temp_password)
    
    def show_register_page(self):
        """Switch to register page"""
        self.stacked_widget.setCurrentWidget(self.register_page)
        
        # Populate fields from temporary data if available
        if hasattr(self.register_page, 'populate_from_temp_data'):
            self.register_page.populate_from_temp_data()
    
    def on_login_successful(self):
        """Handle successful login"""
        try:
            # Check if vault exists for the current user
            user_id = self.auth_manager.current_user['username']  # Simplified for this example
            if self.vault_manager.vault_exists(user_id):
                # Show unlock page
                self.stacked_widget.setCurrentWidget(self.unlock_page)
                self.unlock_page.set_username(self.auth_manager.current_user['username'])
            else:
                # Show unlock page in create mode
                self.stacked_widget.setCurrentWidget(self.unlock_page)
                self.unlock_page.set_username(self.auth_manager.current_user['username'])
                self.unlock_page.set_create_mode()
                
                # Let the user know they need to create a vault
                QMessageBox.information(
                    self,
                    "Create Vault",
                    "This is your first login. You need to create a password vault with a master password."
                )
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error after login: {str(e)}")
    
    def on_unlock_successful(self):
        """Handle successful vault unlock"""
        try:
            # Get the master password from the unlock page
            master_password = self.unlock_page.password_input.text()
            self.current_master_password = master_password
            
            # Set the master password in the vault page
            self.vault_page.set_master_password(master_password)
            
            # Load vault data
            self.vault_page.load_entries()
            self.vault_page.set_username(self.auth_manager.current_user['username'])
            
            # Show vault page
            self.stacked_widget.setCurrentWidget(self.vault_page)
            
            # Clear the password from the unlock page for security
            self.unlock_page.clear_fields()
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error after unlock: {str(e)}")
    
    def lock_vault(self):
        """Lock the vault and show unlock page"""
        try:
            self.vault_manager.lock_vault()
            self.stacked_widget.setCurrentWidget(self.unlock_page)
            self.unlock_page.set_username(self.auth_manager.current_user['username'])
            
            # Clear the current master password for security
            self.current_master_password = None
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error locking vault: {str(e)}")
    
    def logout(self):
        """Logout the current user"""
        try:
            self.auth_manager.logout()
            self.vault_manager.lock_vault()
            self.show_login_page()
            
            # Clear any existing input in the login form
            self.login_page.clear_fields()
            
            # Clear the current master password for security
            self.current_master_password = None
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Error during logout: {str(e)}")
    
    def delete_account(self):
        """Delete the current user's account and all associated data"""
        try:
            # Confirm deletion
            confirmation = QMessageBox.warning(
                self,
                "Delete Account",
                "Are you sure you want to delete your account and all your data? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirmation != QMessageBox.Yes:
                return
            
            # Get current username
            username = self.auth_manager.current_user['username']
            
            # Ask for password confirmation
            from PyQt5.QtWidgets import QInputDialog
            password, ok = QInputDialog.getText(
                self, 
                "Confirm Password", 
                "Enter your password to confirm account deletion:", 
                QLineEdit.Password
            )
            
            if not ok or not password:
                return
            
            # Delete the vault first
            self.vault_manager.delete_user_vault(username)
            
            # Delete the user account
            self.auth_manager.delete_user(username, password)
            
            # Show confirmation and return to login screen
            QMessageBox.information(
                self,
                "Account Deleted",
                "Your account and all associated data have been permanently deleted."
            )
            
            # Go back to login page
            self.show_login_page()
            
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while deleting the account: {str(e)}")
    
    def center(self):
        """Center the window on the screen"""
        frame_geometry = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Default handling for keyboard interrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the error
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"Unhandled exception: {error_msg}")
    
    # Show error dialog
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setText("An unexpected error occurred")
    error_dialog.setInformativeText(str(exc_value))
    error_dialog.setDetailedText(error_msg)
    error_dialog.setWindowTitle("Error")
    error_dialog.exec_()

def main():
    """Main application entry point"""
    # Install global exception handler
    sys.excepthook = handle_exception
    
    # Create application directories if they don't exist
    try:
        app_data_dir = os.path.join(os.path.expanduser('~'), '.secure_vault')
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
    except Exception as e:
        print(f"Error creating application directory: {e}")
        QMessageBox.critical(None, "Initialization Error", 
                            f"Failed to create application directory: {str(e)}")
        return 1
    
    # Create the application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for consistent cross-platform look
    
    try:
        # Create and show the main window
        main_window = PasswordManagerApp()
        main_window.show()
        
        # Start the application event loop
        return app.exec_()
    except Exception as e:
        print(f"Error starting application: {e}")
        QMessageBox.critical(None, "Startup Error", f"Failed to start application: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 