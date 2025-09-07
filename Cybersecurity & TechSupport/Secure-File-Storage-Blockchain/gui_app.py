#!/usr/bin/env python3
"""
Secure File Storage GUI - Modern desktop application
with PyQt5 interface for secure file operations with blockchain verification.
"""

import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QLineEdit, QFileDialog, QTableWidget,
        QTableWidgetItem, QMessageBox, QProgressBar, QDialog, QTextEdit,
        QTabWidget, QGroupBox, QFormLayout, QComboBox, QStatusBar,
        QHeaderView, QSplashScreen, QStyle, QToolBar, QAction, QFrame,
        QStackedWidget, QGridLayout, QCheckBox, QSpacerItem, QSizePolicy,
        QInputDialog, QFileDialog, QListWidget, QListWidgetItem, QSplitter,
        QToolButton, QMenu, QFontDialog, QDialogButtonBox, QScrollArea,
        QPlainTextEdit, QPushButton, QRadioButton, QShortcut
    )
    from PyQt5.QtGui import (
        QIcon, QPixmap, QFont, QColor, QPalette, QCursor, 
        QFontDatabase, QDesktopServices, QKeySequence
    )
    from PyQt5.QtCore import (
        Qt, QSize, QUrl, QThread, pyqtSignal, QTimer, QDateTime,
        QSettings, QFile, QTextStream, QIODevice, QPoint, QEvent,
        QMimeData, QByteArray, QBuffer
    )
except ImportError:
    print("PyQt5 is required. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QLineEdit, QFileDialog, QTableWidget,
        QTableWidgetItem, QMessageBox, QProgressBar, QDialog, QTextEdit,
        QTabWidget, QGroupBox, QFormLayout, QComboBox, QStatusBar,
        QHeaderView, QSplashScreen, QStyle, QToolBar, QAction, QFrame,
        QStackedWidget, QGridLayout, QCheckBox, QSpacerItem, QSizePolicy,
        QInputDialog, QFileDialog, QListWidget, QListWidgetItem, QSplitter,
        QToolButton, QMenu, QFontDialog, QDialogButtonBox, QScrollArea,
        QPlainTextEdit, QPushButton, QRadioButton, QShortcut
    )
    from PyQt5.QtGui import (
        QIcon, QPixmap, QFont, QColor, QPalette, QCursor, 
        QFontDatabase, QDesktopServices, QKeySequence
    )
    from PyQt5.QtCore import (
        Qt, QSize, QUrl, QThread, pyqtSignal, QTimer, QDateTime,
        QSettings, QFile, QTextStream, QIODevice, QPoint, QEvent,
        QMimeData, QByteArray, QBuffer
    )

# Import core modules
try:
    from file_manager import FileManager
    from blockchain import Blockchain
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Make sure the application is installed correctly and you're running from the correct directory.")
    sys.exit(1)

# Constants
APP_NAME = "Secure File Storage"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
DARK_MODE = True

# Colors for dark mode
class Colors:
    DARK_BG = "#2D2D30"
    DARK_ACCENT = "#3E3E42"
    DARK_TEXT = "#FFFFFF"
    DARK_BUTTON = "#1E90FF"
    DARK_BUTTON_HOVER = "#5CB3FF"
    DARK_BUTTON_PRESSED = "#007FFF"
    ACCENT_GREEN = "#4CAF50"
    ACCENT_RED = "#F44336"
    ACCENT_YELLOW = "#FFEB3B"
    ACCENT_BLUE = "#2196F3"
    
    # Light mode colors
    LIGHT_BG = "#F0F0F0"
    LIGHT_ACCENT = "#E0E0E0"
    LIGHT_TEXT = "#212121"
    LIGHT_BUTTON = "#0078D7"
    LIGHT_BUTTON_HOVER = "#429CE3"
    LIGHT_BUTTON_PRESSED = "#005A9E"

# Worker thread for background tasks
class WorkerThread(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, task_type, args=None):
        super().__init__()
        self.task_type = task_type
        self.args = args or {}
        
    def run(self):
        try:
            if self.task_type == "store_file":
                self._store_file()
            elif self.task_type == "retrieve_file":
                self._retrieve_file()
            elif self.task_type == "list_files":
                self._list_files()
            elif self.task_type == "verify_blockchain":
                self._verify_blockchain()
            elif self.task_type == "delete_file":
                self._delete_file()
            elif self.task_type == "file_details":
                self._file_details()
        except Exception as e:
            self.error.emit(str(e))
    
    def _store_file(self):
        file_path = self.args.get("file_path")
        password = self.args.get("password")
        description = self.args.get("description", "")
        
        # Simulate progress
        for i in range(10):
            self.progress.emit(i * 10)
            time.sleep(0.1)
            
        # Actual work
        file_manager = FileManager()
        file_id = file_manager.store_file(file_path, password, description)
        
        self.progress.emit(100)
        self.finished.emit({"file_id": file_id})
        
    def _retrieve_file(self):
        file_id = self.args.get("file_id")
        password = self.args.get("password")
        output_dir = self.args.get("output_dir")
        
        # Simulate progress
        for i in range(10):
            self.progress.emit(i * 10)
            time.sleep(0.1)
            
        # Actual work
        file_manager = FileManager()
        output_path, integrity_verified = file_manager.retrieve_file(file_id, password, output_dir)
        
        self.progress.emit(100)
        self.finished.emit({
            "output_path": output_path,
            "integrity_verified": integrity_verified
        })
        
    def _list_files(self):
        file_manager = FileManager()
        files = file_manager.list_files()
        self.finished.emit({"files": files})
        
    def _verify_blockchain(self):
        file_manager = FileManager()
        result = file_manager.verify_all_files()
        self.finished.emit(result)
        
    def _delete_file(self):
        file_id = self.args.get("file_id")
        file_manager = FileManager()
        success = file_manager.delete_file(file_id)
        self.finished.emit({"success": success})
        
    def _file_details(self):
        file_id = self.args.get("file_id")
        file_manager = FileManager()
        history = file_manager.get_file_history(file_id)
        self.finished.emit({"history": history})

# Password dialog
class PasswordDialog(QDialog):
    def __init__(self, parent=None, confirm=False):
        super().__init__(parent)
        self.confirm = confirm
        self.setWindowTitle("Enter Password")
        self.setFixedWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Password field
        form_layout = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        if self.confirm:
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.Password)
            form_layout.addRow("Confirm Password:", self.confirm_edit)
        
        layout.addLayout(form_layout)
        
        # Requirements and strength meter if confirming
        if self.confirm:
            requirements = QLabel("Password requirements:\n• At least 12 characters\n• Include numbers and special characters")
            requirements.setStyleSheet("color: #888888;")
            layout.addWidget(requirements)
            
            self.strength_bar = QProgressBar()
            self.strength_bar.setRange(0, 100)
            self.strength_bar.setValue(0)
            layout.addWidget(self.strength_bar)
            
            self.password_edit.textChanged.connect(self.update_strength)
            self.confirm_edit.textChanged.connect(self.check_match)
            
            self.match_label = QLabel()
            layout.addWidget(self.match_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def update_strength(self, text):
        # Simple password strength meter
        length_score = min(len(text) * 5, 40)
        has_number = 20 if any(c.isdigit() for c in text) else 0
        has_special = 20 if any(not c.isalnum() for c in text) else 0
        has_upper = 10 if any(c.isupper() for c in text) else 0
        has_lower = 10 if any(c.islower() for c in text) else 0
        
        strength = length_score + has_number + has_special + has_upper + has_lower
        self.strength_bar.setValue(strength)
        
        if strength < 40:
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif strength < 70:
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: yellow; }")
        else:
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            
    def check_match(self):
        if self.password_edit.text() == self.confirm_edit.text():
            self.match_label.setText("Passwords match")
            self.match_label.setStyleSheet("color: green;")
        else:
            self.match_label.setText("Passwords do not match")
            self.match_label.setStyleSheet("color: red;")
            
    def get_password(self):
        if self.confirm:
            if self.password_edit.text() != self.confirm_edit.text():
                return None
        return self.password_edit.text()
        
    def accept(self):
        if self.confirm:
            if self.password_edit.text() != self.confirm_edit.text():
                QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
                return
            
            if len(self.password_edit.text()) < 8:
                QMessageBox.warning(self, "Weak Password", "Password must be at least 8 characters.")
                return
                
            if len(self.password_edit.text()) < 12:
                result = QMessageBox.question(
                    self,
                    "Weak Password",
                    "Password is less than 12 characters. This is considered weak. Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if result != QMessageBox.Yes:
                    return
                    
        super().accept()
        
# Main application window
class SecureStorageApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize file manager
        self.file_manager = FileManager()
        
        # Set window properties
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
        # Load files initially
        self.refresh_file_list()
        
    def setup_ui(self):
        # Create the main widget and layout
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)
        
        # Setup toolbar with actions
        self.setup_toolbar()
        
        # Main content area with tabs
        self.tabs = QTabWidget()
        self.setup_files_tab()
        self.setup_blockchain_tab()
        self.setup_settings_tab()
        
        self.central_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Store file action
        store_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "Store File", self)
        store_action.setStatusTip("Encrypt and store a file securely")
        store_action.triggered.connect(self.store_file)
        toolbar.addAction(store_action)
        
        # Retrieve file action
        retrieve_action = QAction(self.style().standardIcon(QStyle.SP_DialogOpenButton), "Retrieve File", self)
        retrieve_action.setStatusTip("Decrypt and retrieve a stored file")
        retrieve_action.triggered.connect(self.retrieve_file)
        toolbar.addAction(retrieve_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        refresh_action.setStatusTip("Refresh file list")
        refresh_action.triggered.connect(self.refresh_file_list)
        toolbar.addAction(refresh_action)
        
        # Verify blockchain action
        verify_action = QAction(self.style().standardIcon(QStyle.SP_DialogApplyButton), "Verify", self)
        verify_action.setStatusTip("Verify blockchain integrity")
        verify_action.triggered.connect(self.verify_blockchain)
        toolbar.addAction(verify_action)
        
        toolbar.addSeparator()
        
        # About action
        about_action = QAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation), "About", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
        
    def setup_files_tab(self):
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        
        # Quick action buttons
        btn_layout = QHBoxLayout()
        
        store_btn = QPushButton("Store New File")
        store_btn.clicked.connect(self.store_file)
        btn_layout.addWidget(store_btn)
        
        retrieve_btn = QPushButton("Retrieve Selected File")
        retrieve_btn.clicked.connect(self.retrieve_file)
        btn_layout.addWidget(retrieve_btn)
        
        details_btn = QPushButton("View Details")
        details_btn.clicked.connect(self.view_file_details)
        btn_layout.addWidget(details_btn)
        
        delete_btn = QPushButton("Delete File")
        delete_btn.setStyleSheet("background-color: #D32F2F; color: white;")
        delete_btn.clicked.connect(self.delete_file)
        btn_layout.addWidget(delete_btn)
        
        files_layout.addLayout(btn_layout)
        
        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["File ID", "Original Name", "Date", "Description"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SingleSelection)
        self.file_table.itemDoubleClicked.connect(self.view_file_details)
        
        files_layout.addWidget(self.file_table)
        
        # Drag and drop label
        drop_hint = QLabel("Drag and drop files here to store them securely")
        drop_hint.setAlignment(Qt.AlignCenter)
        drop_hint.setStyleSheet("color: #888888;")
        files_layout.addWidget(drop_hint)
        
        self.tabs.addTab(files_widget, "Files")
        
    def setup_blockchain_tab(self):
        blockchain_widget = QWidget()
        blockchain_layout = QVBoxLayout(blockchain_widget)
        
        # Info section
        info_group = QGroupBox("Blockchain Information")
        info_layout = QFormLayout()
        
        self.block_count_label = QLabel("0")
        info_layout.addRow("Total Blocks:", self.block_count_label)
        
        self.last_verified_label = QLabel("Never")
        info_layout.addRow("Last Verified:", self.last_verified_label)
        
        self.blockchain_status_label = QLabel("Unknown")
        info_layout.addRow("Status:", self.blockchain_status_label)
        
        info_group.setLayout(info_layout)
        blockchain_layout.addWidget(info_group)
        
        # Verify button
        verify_btn = QPushButton("Verify Blockchain Integrity")
        verify_btn.clicked.connect(self.verify_blockchain)
        blockchain_layout.addWidget(verify_btn)
        
        # Blockchain visualization (placeholder)
        blockchain_viz = QLabel("Blockchain Visualization")
        blockchain_viz.setAlignment(Qt.AlignCenter)
        blockchain_viz.setMinimumHeight(200)
        blockchain_viz.setStyleSheet("background-color: rgba(0, 0, 0, 0.1); border-radius: 5px;")
        blockchain_layout.addWidget(blockchain_viz)
        
        self.tabs.addTab(blockchain_widget, "Blockchain")
        
    def setup_settings_tab(self):
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        theme_radio_layout = QHBoxLayout()
        self.light_radio = QRadioButton("Light")
        self.dark_radio = QRadioButton("Dark")
        
        if DARK_MODE:
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)
            
        theme_radio_layout.addWidget(self.light_radio)
        theme_radio_layout.addWidget(self.dark_radio)
        theme_layout.addLayout(theme_radio_layout)
        
        self.light_radio.toggled.connect(self.toggle_theme)
        
        theme_group.setLayout(theme_layout)
        settings_layout.addWidget(theme_group)
        
        # Storage settings
        storage_group = QGroupBox("Storage")
        storage_layout = QFormLayout()
        
        self.storage_path_label = QLabel(self.file_manager.storage_dir)
        storage_layout.addRow("Storage Directory:", self.storage_path_label)
        
        storage_group.setLayout(storage_layout)
        settings_layout.addWidget(storage_group)
        
        # About section
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout()
        
        about_text = QLabel(f"{APP_NAME} v{APP_VERSION}\n\nA secure file storage system using encryption and blockchain technology.")
        about_text.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(about_text)
        
        about_group.setLayout(about_layout)
        settings_layout.addWidget(about_group)
        
        # Spacer to push everything up
        settings_layout.addStretch()
        
        self.tabs.addTab(settings_widget, "Settings")
        
    def apply_styles(self):
        """Apply the selected theme styles to the application"""
        if DARK_MODE:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
            
    def apply_dark_theme(self):
        """Apply dark theme styles"""
        style = f"""
        QMainWindow, QDialog, QWidget, QTabWidget::pane {{
            background-color: {Colors.DARK_BG};
            color: {Colors.DARK_TEXT};
        }}
        QTabBar::tab {{
            background-color: {Colors.DARK_ACCENT};
            color: {Colors.DARK_TEXT};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background-color: {Colors.DARK_BG};
            border-bottom: 2px solid {Colors.ACCENT_BLUE};
        }}
        QPushButton {{
            background-color: {Colors.DARK_BUTTON};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.DARK_BUTTON_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {Colors.DARK_BUTTON_PRESSED};
        }}
        QTableWidget {{
            background-color: {Colors.DARK_ACCENT};
            alternate-background-color: {Colors.DARK_BG};
            color: {Colors.DARK_TEXT};
            gridline-color: #555555;
            selection-background-color: {Colors.ACCENT_BLUE};
            selection-color: white;
        }}
        QHeaderView::section {{
            background-color: {Colors.DARK_ACCENT};
            color: {Colors.DARK_TEXT};
            padding: 5px;
            border: 1px solid #555555;
        }}
        QGroupBox {{
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 15px;
            padding-top: 15px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            color: {Colors.DARK_TEXT};
            padding: 0 5px;
        }}
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {Colors.DARK_ACCENT};
            color: {Colors.DARK_TEXT};
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
        }}
        QProgressBar {{
            border: 1px solid #555555;
            border-radius: 3px;
            text-align: center;
            background-color: {Colors.DARK_ACCENT};
        }}
        QProgressBar::chunk {{
            background-color: {Colors.ACCENT_BLUE};
        }}
        QToolBar {{
            background-color: {Colors.DARK_ACCENT};
            border-bottom: 1px solid #555555;
            spacing: 3px;
        }}
        QStatusBar {{
            background-color: {Colors.DARK_ACCENT};
            color: {Colors.DARK_TEXT};
        }}
        """
        self.setStyleSheet(style)
        
    def apply_light_theme(self):
        """Apply light theme styles"""
        style = f"""
        QMainWindow, QDialog, QWidget, QTabWidget::pane {{
            background-color: {Colors.LIGHT_BG};
            color: {Colors.LIGHT_TEXT};
        }}
        QTabBar::tab {{
            background-color: {Colors.LIGHT_ACCENT};
            color: {Colors.LIGHT_TEXT};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background-color: {Colors.LIGHT_BG};
            border-bottom: 2px solid {Colors.LIGHT_BUTTON};
        }}
        QPushButton {{
            background-color: {Colors.LIGHT_BUTTON};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {Colors.LIGHT_BUTTON_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {Colors.LIGHT_BUTTON_PRESSED};
        }}
        QTableWidget {{
            background-color: white;
            alternate-background-color: {Colors.LIGHT_ACCENT};
            color: {Colors.LIGHT_TEXT};
            gridline-color: #CCCCCC;
            selection-background-color: {Colors.LIGHT_BUTTON};
            selection-color: white;
        }}
        QHeaderView::section {{
            background-color: {Colors.LIGHT_ACCENT};
            color: {Colors.LIGHT_TEXT};
            padding: 5px;
            border: 1px solid #CCCCCC;
        }}
        QGroupBox {{
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            margin-top: 15px;
            padding-top: 15px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            color: {Colors.LIGHT_TEXT};
            padding: 0 5px;
        }}
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: white;
            color: {Colors.LIGHT_TEXT};
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            padding: 5px;
        }}
        QProgressBar {{
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {Colors.LIGHT_BUTTON};
        }}
        QToolBar {{
            background-color: {Colors.LIGHT_ACCENT};
            border-bottom: 1px solid #CCCCCC;
            spacing: 3px;
        }}
        QStatusBar {{
            background-color: {Colors.LIGHT_ACCENT};
            color: {Colors.LIGHT_TEXT};
        }}
        """
        self.setStyleSheet(style)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        global DARK_MODE
        DARK_MODE = self.dark_radio.isChecked()
        self.apply_styles()
    
    def refresh_file_list(self):
        """Refresh the file list table"""
        self.statusBar.showMessage("Refreshing file list...")
        
        # Start the worker thread
        self.worker = WorkerThread("list_files")
        self.worker.finished.connect(self.on_files_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_files_loaded(self, result):
        """Handle the results of loading files"""
        files = result.get("files", {})
        
        self.file_table.setRowCount(0)  # Clear table
        
        for row, (file_id, metadata) in enumerate(files.items()):
            self.file_table.insertRow(row)
            self.file_table.setItem(row, 0, QTableWidgetItem(file_id))
            self.file_table.setItem(row, 1, QTableWidgetItem(metadata["original_filename"]))
            
            # Convert timestamp to readable format
            timestamp_str = metadata.get("timestamp", "N/A")
            display_timestamp = "N/A"
            
            if timestamp_str and timestamp_str != "N/A":
                try:
                    # Try different timestamp formats
                    if isinstance(timestamp_str, str):
                        # Format: ISO format (2025-04-27T19:58:47 or 2025-04-27 19:58:47)
                        if "T" in timestamp_str or ("-" in timestamp_str and ":" in timestamp_str):
                            # Handle possible timezone indicator
                            clean_ts = timestamp_str.replace('Z', '+00:00')
                            # Handle format without T separator
                            if "-" in clean_ts and ":" in clean_ts and "T" not in clean_ts:
                                parts = clean_ts.split(" ")
                                if len(parts) == 2:
                                    clean_ts = f"{parts[0]}T{parts[1]}"
                            try:
                                timestamp_obj = datetime.fromisoformat(clean_ts)
                                display_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                # If not standard ISO format, just display as is
                                display_timestamp = timestamp_str
                        # Format: YYYYMMDDHHMMSS (like 20250427195847)
                        elif timestamp_str.isdigit() and len(timestamp_str) == 14:
                            year = timestamp_str[0:4]
                            month = timestamp_str[4:6]
                            day = timestamp_str[6:8]
                            hour = timestamp_str[8:10]
                            minute = timestamp_str[10:12]
                            second = timestamp_str[12:14]
                            display_timestamp = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                        # Format: Unix timestamp (seconds since epoch)
                        elif timestamp_str.isdigit() and len(timestamp_str) <= 10:
                            timestamp_obj = datetime.fromtimestamp(int(timestamp_str))
                            display_timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            # Just use the string as is
                            display_timestamp = timestamp_str
                    else:
                        # Not a string, just convert to string
                        display_timestamp = str(timestamp_str)
                except Exception as e:
                    # Just use the original string if any error
                    display_timestamp = str(timestamp_str)
                    print(f"Warning: Error parsing timestamp '{timestamp_str}': {str(e)}")
            
            self.file_table.setItem(row, 2, QTableWidgetItem(display_timestamp))
            self.file_table.setItem(row, 3, QTableWidgetItem(metadata.get("description", "")))
        
        self.statusBar.showMessage(f"Loaded {len(files)} files", 3000)
    
    def get_selected_file_id(self):
        """Get the currently selected file ID from the table"""
        selected_items = self.file_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a file first.")
            return None
        
        row = selected_items[0].row()
        file_id = self.file_table.item(row, 0).text()
        return file_id
        
    def store_file(self):
        """Store a new file with encryption"""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Store",
            "",
            "All Files (*.*)"
        )
        
        if not file_path:
            return
            
        # Get description
        description, ok = QInputDialog.getText(
            self,
            "File Description",
            "Enter a description for this file (optional):"
        )
        
        if not ok:
            return
            
        # Get password
        password_dialog = PasswordDialog(self, confirm=True)
        if password_dialog.exec_() != QDialog.Accepted:
            return
            
        password = password_dialog.get_password()
        if not password:
            return
            
        # Progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Encrypting File")
        progress_layout = QVBoxLayout(progress_dialog)
        
        status_label = QLabel("Encrypting and storing file...")
        progress_layout.addWidget(status_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_layout.addWidget(progress_bar)
        
        progress_dialog.setFixedSize(400, 100)
        progress_dialog.show()
        
        # Start worker thread
        self.worker = WorkerThread(
            "store_file", 
            {"file_path": file_path, "password": password, "description": description}
        )
        
        self.worker.progress.connect(progress_bar.setValue)
        self.worker.finished.connect(lambda result: self.on_file_stored(result, progress_dialog))
        self.worker.error.connect(lambda err: self.on_error(err, progress_dialog))
        self.worker.start()
    
    def on_file_stored(self, result, dialog=None):
        """Handle completion of file storage operation"""
        if dialog:
            dialog.accept()
            
        file_id = result.get("file_id")
        if file_id:
            QMessageBox.information(
                self,
                "File Stored",
                f"File stored successfully!\nFile ID: {file_id}\n\nKeep this ID and your password safe. There is no way to recover them."
            )
            self.refresh_file_list()
    
    def retrieve_file(self):
        """Retrieve and decrypt a stored file"""
        file_id = self.get_selected_file_id()
        if not file_id:
            return
            
        # Get password
        password_dialog = PasswordDialog(self)
        if password_dialog.exec_() != QDialog.Accepted:
            return
            
        password = password_dialog.get_password()
        
        # Get output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )
        
        if not output_dir:
            return
            
        # Progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Decrypting File")
        progress_layout = QVBoxLayout(progress_dialog)
        
        status_label = QLabel("Retrieving and decrypting file...")
        progress_layout.addWidget(status_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_layout.addWidget(progress_bar)
        
        progress_dialog.setFixedSize(400, 100)
        progress_dialog.show()
        
        # Start worker thread
        self.worker = WorkerThread(
            "retrieve_file", 
            {"file_id": file_id, "password": password, "output_dir": output_dir}
        )
        
        self.worker.progress.connect(progress_bar.setValue)
        self.worker.finished.connect(lambda result: self.on_file_retrieved(result, progress_dialog))
        self.worker.error.connect(lambda err: self.on_error(err, progress_dialog))
        self.worker.start()
    
    def on_file_retrieved(self, result, dialog=None):
        """Handle completion of file retrieval operation"""
        if dialog:
            dialog.accept()
            
        output_path = result.get("output_path")
        integrity_verified = result.get("integrity_verified", False)
        
        if not output_path:
            QMessageBox.critical(self, "Error", "Failed to decrypt the file. Check your password.")
            return
            
        message = f"File retrieved successfully!\nOutput path: {output_path}\n"
        
        if integrity_verified:
            message += "\nBlockchain integrity verification: PASSED"
            QMessageBox.information(self, "File Retrieved", message)
        else:
            message += "\n[WARNING] Blockchain integrity verification: FAILED\nThe file may have been tampered with!"
            QMessageBox.warning(self, "File Retrieved", message)
        
        # Ask if they want to open the folder
        result = QMessageBox.question(
            self,
            "Open File Location",
            "Do you want to open the folder containing the file?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(output_path)))
    
    def delete_file(self):
        """Delete a stored file"""
        file_id = self.get_selected_file_id()
        if not file_id:
            return
            
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this file? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result != QMessageBox.Yes:
            return
            
        # Start worker thread
        self.worker = WorkerThread("delete_file", {"file_id": file_id})
        self.worker.finished.connect(self.on_file_deleted)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_file_deleted(self, result):
        """Handle completion of file deletion operation"""
        success = result.get("success", False)
        
        if success:
            QMessageBox.information(self, "File Deleted", "File deleted successfully.")
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "Error", "Failed to delete the file.")
    
    def view_file_details(self):
        """View detailed information about a file"""
        file_id = self.get_selected_file_id()
        if not file_id:
            return
            
        # Get file metadata
        files = self.file_manager.list_files()
        file_info = files.get(file_id)
        
        if not file_info:
            QMessageBox.critical(self, "Error", "Failed to retrieve file information.")
            return
            
        # Create details dialog
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle("File Details")
        details_dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(details_dialog)
        
        # File information
        info_group = QGroupBox("File Information")
        info_layout = QFormLayout()
        
        info_layout.addRow("File ID:", QLabel(file_id))
        info_layout.addRow("Original Filename:", QLabel(file_info["original_filename"]))
        info_layout.addRow("Description:", QLabel(file_info.get("description", "N/A")))
        info_layout.addRow("Encrypted Path:", QLabel(file_info["encrypted_path"]))
        info_layout.addRow("Created:", QLabel(file_info["timestamp"]))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Loading blockchain history
        status_label = QLabel("Loading blockchain history...")
        layout.addWidget(status_label)
        
        # Start worker thread to load history
        self.worker = WorkerThread("file_details", {"file_id": file_id})
        self.worker.finished.connect(lambda result: self.show_history(result, details_dialog, status_label))
        self.worker.error.connect(lambda err: self.on_error(err, None))
        self.worker.start()
        
        # Show dialog
        details_dialog.exec_()
    
    def show_history(self, result, dialog, status_label):
        """Show blockchain history in the details dialog"""
        history = result.get("history", [])
        
        # Remove status label
        status_label.setParent(None)
        
        # Add history section to dialog
        history_group = QGroupBox("Blockchain History")
        history_layout = QVBoxLayout()
        
        if not history:
            history_layout.addWidget(QLabel("No blockchain history found for this file."))
        else:
            # Create table for history
            history_table = QTableWidget()
            history_table.setColumnCount(3)
            history_table.setHorizontalHeaderLabels(["Block #", "Timestamp", "Hash"])
            history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            for i, entry in enumerate(history):
                history_table.insertRow(i)
                history_table.setItem(i, 0, QTableWidgetItem(str(entry.get("block_index", i+1))))
                
                # Format timestamp
                timestamp = entry.get("timestamp", "")
                if timestamp:
                    timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = timestamp_obj.strftime("%Y-%m-%d %H:%M:%S")
                
                history_table.setItem(i, 1, QTableWidgetItem(timestamp))
                
                # Truncate hash for display
                hash_val = entry.get("hash", "N/A")
                if hash_val != "N/A" and len(hash_val) > 10:
                    hash_val = hash_val[:10] + "..."
                    
                history_table.setItem(i, 2, QTableWidgetItem(hash_val))
                
            history_layout.addWidget(history_table)
            
        history_group.setLayout(history_layout)
        dialog.layout().addWidget(history_group)
    
    def verify_blockchain(self):
        """Verify the integrity of the blockchain"""
        self.statusBar.showMessage("Verifying blockchain integrity...")
        
        # Progress dialog
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Verifying Blockchain")
        progress_layout = QVBoxLayout(progress_dialog)
        
        status_label = QLabel("Verifying blockchain integrity...")
        progress_layout.addWidget(status_label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_layout.addWidget(progress_bar)
        
        progress_dialog.setFixedSize(400, 100)
        progress_dialog.show()
        
        # Start worker thread
        self.worker = WorkerThread("verify_blockchain")
        self.worker.finished.connect(lambda result: self.on_blockchain_verified(result, progress_dialog))
        self.worker.error.connect(lambda err: self.on_error(err, progress_dialog))
        self.worker.start()
    
    def on_blockchain_verified(self, result, dialog=None):
        """Handle completion of blockchain verification"""
        if dialog:
            dialog.accept()
            
        blockchain_valid = result.get("blockchain_valid", False)
        
        # Update blockchain info
        self.last_verified_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        if blockchain_valid:
            self.blockchain_status_label.setText("Valid")
            self.blockchain_status_label.setStyleSheet("color: green;")
            
            QMessageBox.information(
                self,
                "Blockchain Verification",
                "✓ Blockchain integrity verified: PASSED\n\nAll blocks in the blockchain have been verified and the chain is intact."
            )
        else:
            self.blockchain_status_label.setText("Invalid")
            self.blockchain_status_label.setStyleSheet("color: red;")
            
            QMessageBox.critical(
                self,
                "Blockchain Verification",
                "✗ Blockchain integrity verified: FAILED\n\nThe blockchain may have been tampered with! Some blocks have invalid hashes or the chain has been modified."
            )
    
    def show_about(self):
        """Show about dialog with application information"""
        about_text = f"""
        <h2>{APP_NAME} v{APP_VERSION}</h2>
        <p>A secure file storage system that uses strong encryption and blockchain technology to ensure file integrity and security.</p>
        
        <h3>Features</h3>
        <ul>
            <li><b>Strong Encryption:</b> AES-256-CBC encryption with PBKDF2 key derivation</li>
            <li><b>Blockchain Verification:</b> Every file operation is recorded in a blockchain</li>
            <li><b>Metadata Management:</b> Keeps track of all files with metadata</li>
            <li><b>Modern UI:</b> Intuitive and responsive user interface</li>
        </ul>
        
        <h3>Components</h3>
        <ul>
            <li><b>Crypto Module:</b> AES-256-CBC with PBKDF2</li>
            <li><b>Blockchain:</b> Proof-of-Work with SHA-256</li>
            <li><b>File Manager:</b> Metadata and file operations</li>
        </ul>
        
        <h3>Security</h3>
        <p>Your files are encrypted using industry-standard AES-256-CBC encryption.
        The blockchain ensures tamper detection and file integrity verification.</p>
        """
        
        QMessageBox.about(self, f"About {APP_NAME}", about_text)
    
    def on_error(self, error_msg, dialog=None):
        """Handle errors from worker threads"""
        if dialog:
            dialog.accept()
            
        QMessageBox.critical(self, "Error", f"An error occurred: {error_msg}")
        self.statusBar.showMessage(f"Error: {error_msg}", 5000)

# Main entry point
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Show splash screen
    pixmap = QPixmap(300, 300)
    pixmap.fill(QColor(Colors.DARK_BG if DARK_MODE else Colors.LIGHT_BG))
    splash = QSplashScreen(pixmap)
    splash.show()
    
    # Create main window
    window = SecureStorageApp()
    
    # Close splash and show main window
    splash.finish(window)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 