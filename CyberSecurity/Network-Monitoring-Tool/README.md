# Network-Monitoring-Tool

Network Monitoring Tool

The Network Monitoring Tool is a Python-based application designed to monitor network traffic in real-time, detect potential security threats, and block malicious IP addresses. It leverages Scapy for packet capture and analysis and integrates with threat intelligence feeds to identify known malicious IPs.
Features

   - Real-time Packet Capture: Monitors TCP and UDP traffic on selected network interfaces.
   - Threat Detection:
       - Detects SYN flood attacks.
       - Identifies port scanning activities.
       - Alerts on traffic from known malicious IP addresses.
   - Threat Intelligence Integration: Automatically downloads and updates a list of malicious IPs from Emerging Threats.
   - Automatic IP Blocking: Blocks malicious IPs using Windows Firewall or Linux iptables.
   - Customizable Thresholds: Allows configuration of detection thresholds for SYN packets and new ports.
   - Subnet Filtering: Filters traffic based on specified subnets (CIDR format).
   - Multi-Interface Support: Supports monitoring on multiple network interfaces simultaneously.
   - Cross-Platform: Works on both Windows and Linux systems.

### Installation
    Prerequisites

    - Python 3.7 or higher
    - Scapy library: Install via pip install scapy
    - Npcap (Windows) or libpcap (Linux) for packet capture
    - Administrator/root privileges are required for network interface access and firewall manipulation.

    Installation Steps

    Clone the Repository:
    git clone https://github.com/your-repo/network-monitoring-tool.git
    cd network-monitoring-tool

    Install Dependencies:
    pip install -r requirements.txt
    
    Set Up Npcap (Windows):
        Download and install Npcap from the [Npcap website](https://npcap.com/#download).
        Ensure the option "Install in WinPcap API-compatible mode" is checked during installation.

    Set Up libpcap (Linux):
        Install libpcap using your package manager:
        sudo apt-get install libpcap-dev  # For Debian/Ubuntu
        sudo yum install libpcap-devel    # For CentOS/RHEL

### Usage

    Run the Tool:
    python network_monitor.py

    Main Menu:

        Start/Stop Monitoring: Begin or halt network traffic monitoring.
        Change Interface: Select the network interface(s) to monitor.
        Configure Detection Thresholds: Set thresholds for SYN packets and new ports.
        Set Subnet Filter: Filter traffic by subnet (CIDR format).
        View Detected Threats: Display a list of detected security events.
        Update Threat Intelligence: Refresh the list of malicious IPs.
        Exit: Close the application.

    Monitoring:

        Once monitoring starts, the tool will display alerts for detected threats in real-time.
        Press Ctrl+C to stop monitoring.

### Configuration

Thresholds

You can configure the following thresholds in the tool:
    SYN Packets/Minute: The number of SYN packets per minute to trigger a SYN flood alert.
    New Ports/Minute: The number of new ports accessed per minute to trigger a port scan alert.

Subnet Filter

Specify a subnet in CIDR format (e.g., 192.168.1.0/24) to filter traffic and focus on specific network segments.
Threat Intelligence
The tool automatically downloads a list of malicious IPs from Emerging Threats. You can manually update this list using the "Update Threat Intelligence" option in the menu.
Blocking Malicious IPs

When a malicious IP is detected, the tool will automatically block it using:

    Windows: Adds a rule to Windows Firewall.
    Linux: Adds a rule to iptables.

### Troubleshooting

    Permission Errors: Ensure the tool is run with administrator/root privileges.
    Interface Issues: Verify that the selected interface is active and supports packet capture.
    Missing Dependencies: Reinstall Scapy and ensure Npcap/libpcap is correctly installed.

### Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

### Acknowledgements

    Scapy: https://scapy.net/
    Emerging Threats: https://rules.emergingthreats.net/
