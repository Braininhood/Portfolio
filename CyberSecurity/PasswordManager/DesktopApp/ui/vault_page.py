#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vault Page - Main vault interface for managing passwords
"""

from PyQt5.QtWidgets import (QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                            QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QTabWidget, QWidget, QDialog, QFormLayout,
                            QComboBox, QCheckBox, QTextEdit, QDialogButtonBox,
                            QSplitter, QFrame, QToolBar, QAction, QSizePolicy,
                            QMenu, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

import pyperclip
from datetime import datetime

from .base_page import BasePage

class PasswordEntryDialog(QDialog):
    """Dialog for creating or editing a password entry"""
    
    def __init__(self, parent=None, entry=None, password_generator=None, crypto_service=None):
        """Initialize the dialog
        
        Args:
            parent (QWidget, optional): Parent widget
            entry (dict, optional): Entry to edit, or None for new entry
            password_generator (PasswordGenerator, optional): Password generator
            crypto_service (CryptoService, optional): Crypto service for password analysis
        """
        super().__init__(parent)
        
        self.entry = entry or {}
        self.password_generator = password_generator
        self.crypto_service = crypto_service
        
        self.setWindowTitle("Password Entry")
        self.setMinimumWidth(500)
        
        # Set up the UI
        self.setup_ui()
        
        # Populate fields if editing
        if entry:
            self.populate_fields()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Title field
        self.title_input = QLineEdit()
        form_layout.addRow("Title:", self.title_input)
        
        # Username field
        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)
        
        # Password field with generator
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(self.password_input)
        
        # Toggle password visibility
        self.show_password_btn = QPushButton("Show")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)
        
        # Generate password button
        if self.password_generator:
            generate_btn = QPushButton("Generate")
            generate_btn.clicked.connect(self.generate_password)
            password_layout.addWidget(generate_btn)
        
        form_layout.addRow("Password:", password_layout)
        
        # Password strength indicator (if crypto service is available)
        if self.crypto_service:
            strength_layout = QHBoxLayout()
            self.strength_label = QLabel("No password")
            strength_layout.addWidget(self.strength_label)
            form_layout.addRow("Strength:", strength_layout)
            
            # Update strength when password changes
            self.password_input.textChanged.connect(self.update_password_strength)
        
        # URL field
        self.url_input = QLineEdit()
        form_layout.addRow("URL:", self.url_input)
        
        # Category field
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Login", "Credit Card", "Secure Note", "Identity"])
        form_layout.addRow("Category:", self.category_combo)
        
        # Favorite checkbox
        self.favorite_checkbox = QCheckBox("Mark as favorite")
        form_layout.addRow("", self.favorite_checkbox)
        
        # Notes field
        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(100)
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def populate_fields(self):
        """Populate fields with entry data"""
        self.title_input.setText(self.entry.get('title', ''))
        self.username_input.setText(self.entry.get('username', ''))
        self.password_input.setText(self.entry.get('password', ''))
        self.url_input.setText(self.entry.get('url', ''))
        self.notes_input.setText(self.entry.get('notes', ''))
        
        # Set category
        category = self.entry.get('category', 'login').capitalize()
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
        # Set favorite
        self.favorite_checkbox.setChecked(self.entry.get('favorite', False))
        
        # Update strength if available
        if self.crypto_service:
            self.update_password_strength()
    
    def toggle_password_visibility(self, checked):
        """Toggle password visibility"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("Hide")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("Show")
    
    def generate_password(self):
        """Generate a random password"""
        if self.password_generator:
            password = self.password_generator.generate()
            self.password_input.setText(password)
    
    def update_password_strength(self):
        """Update password strength indicator"""
        if self.crypto_service:
            password = self.password_input.text()
            if not password:
                self.strength_label.setText("No password")
                return
            
            # Analyze password strength
            analysis = self.crypto_service.analyze_password_strength(password)
            strength = analysis.get('strength', 'Unknown')
            
            # Set color based on strength
            color = "red"
            if strength == "Very Strong":
                color = "green"
            elif strength == "Strong":
                color = "lightgreen"
            elif strength == "Moderate":
                color = "orange"
            elif strength == "Weak":
                color = "darkorange"
                
            self.strength_label.setText(strength)
            self.strength_label.setStyleSheet(f"color: {color};")
    
    def get_entry_data(self):
        """Get the entry data from the form
        
        Returns:
            dict: Entry data
        """
        return {
            'title': self.title_input.text().strip(),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),
            'url': self.url_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'category': self.category_combo.currentText().lower(),
            'favorite': self.favorite_checkbox.isChecked()
        }

class VaultPage(BasePage):
    """Main vault page for managing password entries"""
    
    # Signals
    lock_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    
    def __init__(self, vault_manager, password_generator):
        """Initialize the vault page
        
        Args:
            vault_manager (VaultManager): Vault manager
            password_generator (PasswordGenerator): Password generator
        """
        super().__init__()
        
        self.vault_manager = vault_manager
        self.password_generator = password_generator
        self.username = ""
        self.entries = []
        self.current_filter = {}
        self.master_password = None  # Store the master password for vault operations
        
        # Set up the UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Add entry button
        add_action = QAction("Add Entry", self)
        add_action.triggered.connect(self.add_entry)
        toolbar.addAction(add_action)
        
        toolbar.addSeparator()
        
        # Search field
        search_label = QLabel("Search:")
        toolbar.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.search_entries)
        toolbar.addWidget(self.search_input)
        
        # Add spacer to push the next items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Delete Account button
        delete_account_action = QAction("Delete Account", self)
        delete_account_action.triggered.connect(self.delete_account)
        toolbar.addAction(delete_account_action)
        
        # Add toolbar to layout
        self.main_layout.addWidget(toolbar)
        
        # Create splitter for sidebar and main content
        splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setMaximumWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Category filters
        sidebar_layout.addWidget(self.create_subtitle("Categories"))
        
        # All entries button
        all_btn = QPushButton("All Items")
        all_btn.clicked.connect(lambda: self.filter_entries({}))
        sidebar_layout.addWidget(all_btn)
        
        # Favorites button
        favorites_btn = QPushButton("Favorites")
        favorites_btn.clicked.connect(lambda: self.filter_entries({'favorite': True}))
        sidebar_layout.addWidget(favorites_btn)
        
        # Category buttons
        for category in ["Login", "Credit Card", "Secure Note", "Identity"]:
            cat_btn = QPushButton(category)
            cat_btn.clicked.connect(lambda checked, c=category: self.filter_entries({'category': c.lower()}))
            sidebar_layout.addWidget(cat_btn)
        
        sidebar_layout.addStretch()
        
        # User info and logout
        user_frame = QFrame()
        user_layout = QVBoxLayout(user_frame)
        
        self.username_label = QLabel("")
        user_layout.addWidget(self.username_label)
        
        lock_btn = QPushButton("Lock Vault")
        lock_btn.clicked.connect(self.lock_vault)
        user_layout.addWidget(lock_btn)
        
        logout_btn = QPushButton("Log Out")
        logout_btn.clicked.connect(self.logout)
        user_layout.addWidget(logout_btn)
        
        sidebar_layout.addWidget(user_frame)
        
        # Main content - entries table
        content = QFrame()
        content_layout = QVBoxLayout(content)
        
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(4)
        self.entries_table.setHorizontalHeaderLabels(["Title", "Username", "Category", "Last Modified"])
        self.entries_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.entries_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.entries_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.edit_entry)
        self.entries_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entries_table.customContextMenuRequested.connect(self.show_context_menu)
        
        content_layout.addWidget(self.entries_table)
        
        # Add sidebar and content to splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(content)
        
        # Add splitter to main layout
        self.main_layout.addWidget(splitter)
    
    def set_username(self, username):
        """Set the current username
        
        Args:
            username (str): Current username
        """
        self.username = username
        self.username_label.setText(f"User: {username}")
    
    def set_master_password(self, password):
        """Set the master password for vault operations
        
        Args:
            password (str): Master password
        """
        self.master_password = password
    
    def load_entries(self):
        """Load password entries from the vault"""
        try:
            self.entries = self.vault_manager.get_all_entries()
            self.display_entries(self.entries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load entries: {str(e)}")
    
    def display_entries(self, entries):
        """Display entries in the table
        
        Args:
            entries (list): List of entries to display
        """
        self.entries_table.setRowCount(0)
        
        for row, entry in enumerate(entries):
            self.entries_table.insertRow(row)
            
            # Title
            title_item = QTableWidgetItem(entry.get('title', ''))
            if entry.get('favorite', False):
                title_item.setIcon(QIcon.fromTheme("emblem-favorite"))
            self.entries_table.setItem(row, 0, title_item)
            
            # Username
            self.entries_table.setItem(row, 1, QTableWidgetItem(entry.get('username', '')))
            
            # Category
            category = entry.get('category', 'login').capitalize()
            self.entries_table.setItem(row, 2, QTableWidgetItem(category))
            
            # Last modified
            last_modified = entry.get('last_modified', '')
            if last_modified:
                try:
                    # Format the ISO date
                    date_obj = datetime.fromisoformat(last_modified)
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    formatted_date = last_modified
            else:
                formatted_date = ""
            
            self.entries_table.setItem(row, 3, QTableWidgetItem(formatted_date))
            
            # Store the entry ID as item data for reference
            title_item.setData(Qt.UserRole, entry.get('id'))
    
    def add_entry(self):
        """Add a new password entry"""
        try:
            # Check if we have a master password
            if not self.master_password:
                self.request_master_password()
                if not self.master_password:  # User canceled
                    return
            
            # Create dialog
            dialog = PasswordEntryDialog(
                self, 
                password_generator=self.password_generator,
                crypto_service=self.vault_manager.crypto_service
            )
            
            if dialog.exec_() == QDialog.Accepted:
                # Get entry data from form
                entry_data = dialog.get_entry_data()
                
                # Validate
                if not entry_data['title']:
                    QMessageBox.warning(self, "Validation Error", "Title is required")
                    return
                
                # Add to vault
                new_entry = self.vault_manager.add_entry(entry_data)
                
                # Save vault
                self.vault_manager.save_vault(self.username, self.master_password)
                
                # Refresh entries
                self.load_entries()
                
                # Show success message
                QMessageBox.information(self, "Success", "Entry added successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add entry: {str(e)}")
    
    def edit_entry(self, index=None):
        """Edit a password entry
        
        Args:
            index (QModelIndex, optional): Index of the entry to edit
        """
        try:
            # Check if we have a master password
            if not self.master_password:
                self.request_master_password()
                if not self.master_password:  # User canceled
                    return
            
            # Get the selected row
            if isinstance(index, bool) or index is None:
                selected_rows = self.entries_table.selectionModel().selectedRows()
                if not selected_rows:
                    return
                index = selected_rows[0]
            
            # Get the entry ID from the table
            entry_id = self.entries_table.item(index.row(), 0).data(Qt.UserRole)
            
            # Get the entry from the vault
            entry = self.vault_manager.get_entry(entry_id)
            if not entry:
                QMessageBox.warning(self, "Error", "Entry not found")
                return
            
            # Create dialog
            dialog = PasswordEntryDialog(
                self, 
                entry=entry,
                password_generator=self.password_generator,
                crypto_service=self.vault_manager.crypto_service
            )
            
            if dialog.exec_() == QDialog.Accepted:
                # Get updated entry data from form
                updated_data = dialog.get_entry_data()
                
                # Validate
                if not updated_data['title']:
                    QMessageBox.warning(self, "Validation Error", "Title is required")
                    return
                
                # Update in vault
                self.vault_manager.update_entry(entry_id, updated_data)
                
                # Save vault
                self.vault_manager.save_vault(self.username, self.master_password)
                
                # Refresh entries
                self.load_entries()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit entry: {str(e)}")
    
    def delete_entry(self):
        """Delete a password entry"""
        try:
            # Check if we have a master password
            if not self.master_password:
                self.request_master_password()
                if not self.master_password:  # User canceled
                    return
            
            # Get the selected row
            selected_rows = self.entries_table.selectionModel().selectedRows()
            if not selected_rows:
                return
            
            # Confirm deletion
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                "Are you sure you want to delete this entry? This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
            
            # Get the entry ID from the table
            entry_id = self.entries_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
            
            # Delete from vault
            if self.vault_manager.delete_entry(entry_id):
                # Save vault
                self.vault_manager.save_vault(self.username, self.master_password)
                
                # Refresh entries
                self.load_entries()
                
                # Show success message
                QMessageBox.information(self, "Success", "Entry deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete entry")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete entry: {str(e)}")
    
    def request_master_password(self):
        """Request the master password from the user"""
        password, ok = QInputDialog.getText(
            self, 
            "Master Password Required", 
            "Please enter your master password to complete this action:",
            QLineEdit.Password
        )
        
        if ok and password:
            self.master_password = password
            return True
        
        return False
    
    def copy_username(self):
        """Copy the username to the clipboard"""
        try:
            # Get the selected row
            selected_rows = self.entries_table.selectionModel().selectedRows()
            if not selected_rows:
                return
            
            # Get the entry ID from the table
            entry_id = self.entries_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
            
            # Get the entry from the vault
            entry = self.vault_manager.get_entry(entry_id)
            if not entry:
                return
            
            # Copy username to clipboard
            username = entry.get('username', '')
            pyperclip.copy(username)
            
            # Show confirmation
            QMessageBox.information(self, "Copied", "Username copied to clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy username: {str(e)}")
    
    def copy_password(self):
        """Copy the password to the clipboard"""
        try:
            # Get the selected row
            selected_rows = self.entries_table.selectionModel().selectedRows()
            if not selected_rows:
                return
            
            # Get the entry ID from the table
            entry_id = self.entries_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
            
            # Get the entry from the vault
            entry = self.vault_manager.get_entry(entry_id)
            if not entry:
                return
            
            # Copy password to clipboard
            password = entry.get('password', '')
            pyperclip.copy(password)
            
            # Show confirmation
            QMessageBox.information(self, "Copied", "Password copied to clipboard")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy password: {str(e)}")
    
    def show_context_menu(self, position):
        """Show context menu for entries table
        
        Args:
            position (QPoint): Position for the menu
        """
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(self.edit_entry)
        
        menu.addSeparator()
        
        copy_username_action = menu.addAction("Copy Username")
        copy_username_action.triggered.connect(self.copy_username)
        
        copy_password_action = menu.addAction("Copy Password")
        copy_password_action.triggered.connect(self.copy_password)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_entry)
        
        # Show menu
        menu.exec_(self.entries_table.viewport().mapToGlobal(position))
    
    def search_entries(self, query):
        """Search entries based on query
        
        Args:
            query (str): Search query
        """
        try:
            # Get entries matching the query
            results = self.vault_manager.search_entries(query)
            
            # Apply current filter to search results if needed
            if self.current_filter:
                results = self.apply_filter(results, self.current_filter)
            
            # Display results
            self.display_entries(results)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to search entries: {str(e)}")
    
    def filter_entries(self, filter_criteria):
        """Filter entries based on criteria
        
        Args:
            filter_criteria (dict): Filter criteria
        """
        try:
            # Store current filter
            self.current_filter = filter_criteria
            
            # Clear search
            self.search_input.clear()
            
            # Get filtered entries
            if filter_criteria:
                filtered_entries = self.vault_manager.filter_entries(filter_criteria)
            else:
                filtered_entries = self.vault_manager.get_all_entries()
            
            # Display filtered entries
            self.display_entries(filtered_entries)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to filter entries: {str(e)}")
    
    def apply_filter(self, entries, filter_criteria):
        """Apply filter criteria to a list of entries
        
        Args:
            entries (list): List of entries
            filter_criteria (dict): Filter criteria
            
        Returns:
            list: Filtered entries
        """
        if not filter_criteria:
            return entries
        
        filtered = entries
        
        # Filter by category
        if 'category' in filter_criteria:
            filtered = [e for e in filtered if e.get('category') == filter_criteria['category']]
        
        # Filter favorites
        if filter_criteria.get('favorite') is True:
            filtered = [e for e in filtered if e.get('favorite') is True]
        
        return filtered
    
    def lock_vault(self):
        """Lock the vault"""
        self.vault_manager.lock_vault()
        self.master_password = None  # Clear master password when locking
        self.lock_requested.emit()
    
    def logout(self):
        """Logout the current user"""
        self.vault_manager.lock_vault()
        self.master_password = None  # Clear master password on logout
        self.logout_requested.emit()
    
    def delete_account(self):
        """Request account deletion"""
        # Send signal to the main window to handle account deletion
        # The main window will already have the necessary setup for this
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'delete_account'):
                parent.delete_account()
                return
            parent = parent.parent()
        
        # If we can't find the main window, show an error
        QMessageBox.warning(self, "Error", "Could not access account management functions.") 