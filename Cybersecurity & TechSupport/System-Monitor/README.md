# System-Monitor

A comprehensive real-time system monitoring tool that provides insights into system health, processes, network usage, and memory management. This utility can be used to identify potential issues like high resource usage, memory leaks, or vulnerable processes.

## Features
- **System Health Monitoring**: CPU, memory, disk, and swap usage.
- **Process Management**: View and filter processes (hidden, vulnerable, or network-related).
- **Network Usage**: Monitor sent/received bytes and IP addresses in real-time.
- **Memory Leak Detection**: Identify processes consuming excessive memory.
- **Customizable Update Intervals**: Adjust monitoring frequency.

## Requirements
This script requires Python 3.6+ and the following libraries:
- `psutil`: This is for accessing the system and processing information.
- `termcolor`: For colored terminal output.

You can install the dependencies using pip:
```bash
pip install psutil termcolor

Usage

    Clone or download the repository.
    Run the script:

    python system_monitor.py

    Navigate through the menu to explore different monitoring features.

Menu Options

    System Health: Displays real-time CPU, memory, disk, and swap usage.
    Processes: Lists running processes and allows filtering by:
        Hidden processes
        Vulnerable processes
        Network-related processes
    Network Usage: Shows current network activity and IP addresses.
    Warnings: Highlights critical system health warnings.
    Memory Leaks: Detects and lists processes with potential memory leaks.

Supported Platforms

    Windows
    Linux
    macOS

Customization

You can adjust the monitoring interval directly in the menu or modify the script to suit specific needs.
