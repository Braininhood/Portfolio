"""
PC Hardware Checker Package
Complete system hardware detection and reporting tool
"""

__version__ = "1.2.0"
__author__ = "PC Hardware Checker Team"
__description__ = "User-friendly PC hardware detection and reporting tool"

from .hardware_detector import HardwareDetector
from .gui_components import ModernGUI

__all__ = ['HardwareDetector', 'ModernGUI']
