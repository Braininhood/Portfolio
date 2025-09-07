#!/usr/bin/env python3
"""
Formatting utilities for professional display
"""

def format_number(value, decimal_places=2, unit=""):
    """
    Format numbers in a professional, readable way
    Avoids scientific notation and provides clean formatting
    """
    if value is None:
        return "N/A"
    
    try:
        # Convert to float if needed
        if isinstance(value, str):
            value = float(value)
        
        # Handle very small numbers
        if abs(value) < 0.01 and value != 0:
            if abs(value) < 0.0001:
                return f"0.00{unit}"
            else:
                return f"{value:.4f}{unit}"
        
        # Handle normal numbers
        if abs(value) >= 1000000000:  # Billions
            return f"{value/1000000000:.{decimal_places}f}B{unit}"
        elif abs(value) >= 1000000:  # Millions
            return f"{value/1000000:.{decimal_places}f}M{unit}"
        elif abs(value) >= 1000:  # Thousands
            return f"{value/1000:.{decimal_places}f}K{unit}"
        else:
            return f"{value:.{decimal_places}f}{unit}"
            
    except (ValueError, TypeError):
        return "N/A"

def format_bytes(bytes_value, decimal_places=2):
    """Format bytes in human readable format"""
    if bytes_value is None or bytes_value < 0:
        return "N/A"
    
    try:
        bytes_value = float(bytes_value)
        
        if bytes_value >= 1024**4:  # TB
            return f"{bytes_value / (1024**4):.{decimal_places}f} TB"
        elif bytes_value >= 1024**3:  # GB
            return f"{bytes_value / (1024**3):.{decimal_places}f} GB"
        elif bytes_value >= 1024**2:  # MB
            return f"{bytes_value / (1024**2):.{decimal_places}f} MB"
        elif bytes_value >= 1024:  # KB
            return f"{bytes_value / 1024:.{decimal_places}f} KB"
        else:
            return f"{bytes_value:.0f} B"
            
    except (ValueError, TypeError):
        return "N/A"

def format_speed(speed_bps, decimal_places=2):
    """Format speed in bps to human readable format"""
    if speed_bps is None or speed_bps < 0:
        return "0.00 B/s"
    
    try:
        speed_bps = float(speed_bps)
        
        if speed_bps >= 1024**3:  # GB/s
            return f"{speed_bps / (1024**3):.{decimal_places}f} GB/s"
        elif speed_bps >= 1024**2:  # MB/s
            return f"{speed_bps / (1024**2):.{decimal_places}f} MB/s"
        elif speed_bps >= 1024:  # KB/s
            return f"{speed_bps / 1024:.{decimal_places}f} KB/s"
        else:
            return f"{speed_bps:.{decimal_places}f} B/s"
            
    except (ValueError, TypeError):
        return "0.00 B/s"

def format_frequency(freq_hz, decimal_places=2):
    """Format frequency in Hz to readable format"""
    if freq_hz is None or freq_hz <= 0:
        return "N/A"
    
    try:
        freq_hz = float(freq_hz)
        
        if freq_hz >= 1000000000:  # GHz
            return f"{freq_hz / 1000000000:.{decimal_places}f} GHz"
        elif freq_hz >= 1000000:  # MHz
            return f"{freq_hz / 1000000:.{decimal_places}f} MHz"
        elif freq_hz >= 1000:  # KHz
            return f"{freq_hz / 1000:.{decimal_places}f} KHz"
        else:
            return f"{freq_hz:.{decimal_places}f} Hz"
            
    except (ValueError, TypeError):
        return "N/A"

def format_temperature(temp_celsius, decimal_places=1):
    """Format temperature with proper handling"""
    if temp_celsius is None or temp_celsius <= 0:
        return "N/A"
    
    try:
        temp_celsius = float(temp_celsius)
        return f"{temp_celsius:.{decimal_places}f}°C"
    except (ValueError, TypeError):
        return "N/A"

def format_percentage(value, decimal_places=1):
    """Format percentage values"""
    if value is None:
        return "N/A"
    
    try:
        value = float(value)
        return f"{value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "N/A"

def format_time_duration(seconds, show_ms=False):
    """Format time duration in human readable format"""
    if seconds is None or seconds < 0:
        return "N/A"
    
    try:
        seconds = float(seconds)
        
        if seconds < 1 and show_ms:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
            
    except (ValueError, TypeError):
        return "N/A"
