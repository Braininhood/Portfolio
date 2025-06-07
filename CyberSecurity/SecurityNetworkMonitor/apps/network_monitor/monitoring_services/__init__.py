"""
Network Monitor Services Package

This package contains various network monitoring services:
- traffic_monitor: Real-time traffic monitoring and analysis
"""

# Only import from the traffic_monitor.py file to avoid circular imports
from .traffic_monitor import RealTimeTrafficMonitor, get_traffic_monitor

__all__ = [
    'RealTimeTrafficMonitor',
    'get_traffic_monitor'
] 