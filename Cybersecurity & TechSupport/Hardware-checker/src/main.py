#!/usr/bin/env python3
"""
PC Hardware Checker - Comprehensive System Information Tool
Compatible with various Windows versions
Easy-to-use interface for non-technical users
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
from datetime import datetime
import threading

# Add current directory and src to path for PyInstaller compatibility
if hasattr(sys, 'frozen'):
    # Running as compiled executable
    current_dir = os.path.dirname(sys.executable)
    src_dir = os.path.join(current_dir, 'src')
else:
    # Running as script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = current_dir

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try multiple import strategies
try:
    from hardware_detector import HardwareDetector
    from gui_components import ModernGUI
except ImportError:
    try:
        from .hardware_detector import HardwareDetector
        from .gui_components import ModernGUI
    except ImportError:
        try:
            import src.hardware_detector as hardware_detector
            import src.gui_components as gui_components
            HardwareDetector = hardware_detector.HardwareDetector
            ModernGUI = gui_components.ModernGUI
        except ImportError as e:
            print(f"Import error: {e}")
            print("Available modules:", [m for m in sys.modules.keys() if 'hardware' in m or 'gui' in m])
            raise


class PCHardwareChecker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PC Hardware Checker - Complete System Information")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize hardware detector
        self.detector = HardwareDetector()
        
        # Initialize GUI
        self.gui = ModernGUI(self.root, self.detector)
        
        # Set window icon and configure
        self.setup_window()
        
    def setup_window(self):
        """Configure the main window"""
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # Center the window
        self.center_window()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        pos_x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        pos_y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"Application error: {str(e)}")


def main():
    """Main entry point"""
    try:
        app = PCHardwareChecker()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
