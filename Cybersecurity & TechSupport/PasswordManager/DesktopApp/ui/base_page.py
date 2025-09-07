#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Page - Base class for UI pages
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class BasePage(QWidget):
    """Base class for all UI pages"""
    
    def __init__(self):
        """Initialize the base page"""
        super().__init__()
        
        # Set up the main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(15)
        
        # Common fonts
        self.title_font = QFont()
        self.title_font.setPointSize(16)
        self.title_font.setBold(True)
        
        self.subtitle_font = QFont()
        self.subtitle_font.setPointSize(12)
        self.subtitle_font.setBold(True)
        
        self.text_font = QFont()
        self.text_font.setPointSize(10)
    
    def create_title(self, text):
        """Create a title label
        
        Args:
            text (str): Title text
            
        Returns:
            QLabel: Title label
        """
        title = QLabel(text)
        title.setFont(self.title_font)
        title.setAlignment(Qt.AlignCenter)
        return title
    
    def create_subtitle(self, text):
        """Create a subtitle label
        
        Args:
            text (str): Subtitle text
            
        Returns:
            QLabel: Subtitle label
        """
        subtitle = QLabel(text)
        subtitle.setFont(self.subtitle_font)
        return subtitle
    
    def create_button(self, text, on_click=None, primary=False):
        """Create a styled button
        
        Args:
            text (str): Button text
            on_click (function, optional): Click handler
            primary (bool, optional): Whether this is a primary button
            
        Returns:
            QPushButton: Button
        """
        button = QPushButton(text)
        button.setMinimumHeight(40)
        
        if primary:
            button.setProperty("class", "primary")
        
        if on_click:
            button.clicked.connect(on_click)
        
        return button
    
    def show_message(self, message, error=False):
        """Show a message to the user (to be implemented by subclasses)
        
        Args:
            message (str): Message to show
            error (bool, optional): Whether this is an error message
        """
        pass 