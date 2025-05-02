# Network-Monitoring-Tool

An advanced network monitoring tool built with Python and Scapy that detects potential security threats like port scans and SYN floods.

## Features

- Real-time network traffic monitoring
- **Port scan detection** - Identifies when an IP address attempts to access multiple ports in a short time
- **SYN flood detection** - Detects potential denial-of-service attacks with excessive SYN packets
- **Malicious IP detection** using threat intelligence database
- **Full IPv4 and IPv6 support**
- **Custom malicious IP management**
- **Comprehensive Help & Usage Guide** built into the application
- Graphical user interface with CustomTkinter
- Support for multiple network interfaces
- Network traffic statistics
- Alerts for potential security threats

## Requirements

### Windows:
- Python 3.8 or higher
- [Npcap](https://npcap.com/#download) for packet capture (recommended)
- Administrator privileges

### Linux:
- Python 3.8 or higher
- Root privileges
- libpcap (usually pre-installed)

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
    pip install -r requirements.txt
```

3. **Windows only:** Download and install [Npcap](https://npcap.com/#download)
   - During installation, select "WinPcap API-compatible Mode"
   - This tool will not function correctly without Npcap installed

## Usage

### Windows:
Simply run the `Start_Network_Monitor.bat` file to launch the GUI.

### Linux:
Run the tool with root privileges:

```bash
sudo python GUI_Network_Monitor.py
```

## GUI Interface

The interface is divided into several sections:

1. **Network Controls**: 
   - Start/Stop monitoring
   - Select network interface
   - Monitor all interfaces at once
   - Access the comprehensive Help & Usage Guide

2. **Threat Detection**:
   - Configure detection thresholds for various attack types
   - Adjust sensitivity based on your network environment

3. **Filtering Options**:
   - Set subnet filters to focus monitoring on specific network segments
   - Add custom malicious IP addresses to the threat database
   - View and manage user-added malicious IPs
   - Update threat intelligence database

4. **Monitoring Tabs**:
   - Live Monitor: Shows real-time network activity
   - Detected Threats: Lists all potential security threats found
   - Statistics: Displays monitoring session statistics

## Threat Detection Capabilities

The tool can detect several types of network security threats:

1. **Port Scans**: 
   - Detects when a single IP address accesses multiple ports in a short timeframe
   - Configurable threshold for detection sensitivity

2. **SYN Floods**: 
   - Identifies potential DoS attacks where excessive SYN packets are detected
   - Configurable threshold to adapt to different network environments

3. **Malicious IP Traffic**: 
   - Automatically alerts when traffic is detected from known malicious IPs
   - Uses both built-in threat intelligence and user-defined malicious IPs

## Custom Malicious IP Management

The tool allows you to add your own known malicious IP addresses to the threat database:

1. Enter an IPv4 or IPv6 address in the "Add Custom Malicious IP" field
2. Click "Add to Threat Database"
3. View your added IPs by clicking "Show User-added IPs"

All user-added IPs are:
- Saved to `user_added_ips.txt`
- Preserved when updating the threat intelligence database
- Used for detecting malicious traffic alongside the main database

## IPv6 Support

This tool fully supports both IPv4 and IPv6 monitoring:

- Detects threats from both IPv4 and IPv6 sources
- Can add IPv4 and IPv6 addresses to the custom threat database
- Displays IP version (IPv4/IPv6) in alerts and logs
- Supports CIDR notation for both IPv4 and IPv6 subnets in the subnet filter

## Raw Socket Mode vs. Npcap Mode

This tool can run in two modes:

1. **Npcap Mode (Preferred)**
   - Uses Npcap drivers for packet capture
   - More reliable and provides more detailed packet information
   - Required for some advanced features
   - Shows interfaces with NPF prefixes in debug logs

2. **Raw Socket Mode (Fallback)**
   - Used when Npcap isn't detected or doesn't work properly
   - Limited functionality compared to Npcap mode
   - May not capture all packets or provide all packet details
   - Shows "Using default interface (raw socket mode)" in logs

The tool automatically tries to use Npcap mode first, then falls back to raw socket mode if needed.

## Help & Usage Guide

A comprehensive help guide is built into the application, accessible via the "Help & Usage Guide" button. This guide includes:

- Detailed explanations of all features
- Instructions for configuring threat detection thresholds
- Guidance on interface selection
- Troubleshooting tips
- Information about filtering options

## Troubleshooting

### Common Issues:

1. **"No valid sniffing interfaces found!"**
   - Make sure [Npcap](https://npcap.com/#download) is installed (Windows only)
   - Run the application with administrator privileges
   - The tool will automatically fall back to raw socket mode if Npcap interfaces aren't found

2. **Interface selection issues**
   - Try using the "Monitor All Interfaces" button
   - If a specific interface isn't working, try another one
   - Look for interfaces that show an IP address in parentheses - these are most likely to work

3. **Error starting monitoring**
   - Verify Npcap is properly installed
   - Make sure you're running with administrator privileges
   - Check that the selected interface is connected and active
   - Try disabling any VPN software temporarily

### Installing Npcap

For Windows users, Npcap is recommended for best performance:

1. Download Npcap from: https://npcap.com/#download
2. Run the installer and follow the instructions
3. **Important settings during installation:**
   - Select "Install Npcap in WinPcap API-compatible Mode"
   - Select "Install Npcap driver"
   - Select "Enable DLT_NULL fixup" (recommended)
4. Restart your computer after installation
5. Run the Network Monitoring Tool as Administrator

## CLI Version

A command-line version is also available. Run it with:

```bash
python network_Monitoring_Tool.py
```

Follow the prompts to select your interface and start monitoring.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for educational and network security assessment purposes only. Always use responsibly and only on networks you own or have permission to monitor.
