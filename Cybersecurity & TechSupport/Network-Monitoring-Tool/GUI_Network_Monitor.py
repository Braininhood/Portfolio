import tkinter as tk
import customtkinter as ctk
import threading
import time
import datetime
import sys
import os
from PIL import Image, ImageTk
import queue
from pathlib import Path
import platform
import socket
import subprocess

# Modify sys.path to handle imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override the get_windows_if_list before importing NetworkMonitor
import scapy.all
from scapy.all import get_if_list, IP, TCP, UDP, sniff, conf

# Fix for missing get_windows_if_list
def custom_get_windows_if_list():
    """Improved implementation that detects all Windows network interfaces"""
    interfaces = []
    try:
        # More reliable approach using netsh first
        netsh_output = subprocess.check_output("netsh interface show interface", shell=True).decode('utf-8', errors='ignore')
        
        # Split the output into lines and skip the header (first 3 lines)
        lines = netsh_output.splitlines()[3:]
        
        # Process each line from netsh (most reliable source)
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Split by multiple spaces
            parts = [p for p in line.split("  ") if p.strip()]
            if len(parts) >= 4:
                # The last part is the interface name
                iface_name = parts[-1].strip()
                status = parts[0].strip()
                
                # Skip disconnected or disabled interfaces
                if "disconnected" in status.lower() and "wi-fi" not in iface_name.lower():
                    continue
                    
                # Try to get IP address
                ip_address = None
                try:
                    ip_info = subprocess.check_output(f'netsh interface ip show addresses "{iface_name}" | findstr "IP Address"', shell=True).decode('utf-8', errors='ignore')
                    if "IP Address" in ip_info:
                        ip_address = ip_info.split(":", 1)[1].strip()
                except:
                    pass
                
                display_name = f"{iface_name}"
                if ip_address:
                    display_name += f" ({ip_address})"
                
                iface_obj = {
                    'name': display_name,
                    'description': f"Status: {status}",
                    'guid': f"netsh-iface-{idx}",
                    'mac': '00:00:00:00:00:00',  # placeholder
                    'win_index': idx,
                    'scapy_name': None  # Will use default interface
                }
                interfaces.append(iface_obj)
        
        # If we found interfaces from netsh, don't try other methods
        if interfaces:
            print(f"[INFO] Detected {len(interfaces)} network interfaces using netsh")
            return interfaces
    except Exception as e:
        print(f"Error getting Windows interfaces via netsh: {e}")
    
    # Fallback to ipconfig method
    try:
        # Direct approach using ipconfig
        ipconfig_output = subprocess.check_output("ipconfig /all", shell=True).decode('utf-8', errors='ignore')
        
        # Parse ipconfig output properly
        sections = ipconfig_output.split("\r\n\r\n")
        
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.splitlines()
            if not lines:
                continue
                
            # The first line contains the interface name
            iface_name = lines[0].rstrip(':')
            if not iface_name or "Windows IP Configuration" in iface_name:
                continue
                
            # Skip entries that aren't actual adapters
            if not any(keyword in iface_name.lower() for keyword in ["adapter", "ethernet", "wi-fi", "wireless"]):
                continue
                
            # Extract useful information
            ip_address = None
            description = None
            
            for line in lines[1:]:
                line = line.strip()
                
                # Look for IPv4 address
                if "IPv4 Address" in line and ":" in line:
                    ip_address = line.split(":", 1)[1].strip().rstrip('(Preferred)')
                
                # Look for description
                elif "Description" in line and ":" in line:
                    description = line.split(":", 1)[1].strip()
            
            # Skip interfaces with "Media disconnected" unless they're wireless (which might reconnect)
            if any("Media disconnected" in line for line in lines) and "wi-fi" not in iface_name.lower():
                continue
                
            # Create display name
            display_name = iface_name
            if ip_address:
                display_name += f" ({ip_address})"
                
            # Add the interface
            iface_obj = {
                'name': display_name,
                'description': description or "No description available",
                'guid': f"iface-{len(interfaces)}",
                'mac': '00:00:00:00:00:00',  # placeholder
                'win_index': len(interfaces),
                'scapy_name': None  # Will use default interface
            }
            interfaces.append(iface_obj)
    except Exception as e:
        print(f"Error getting Windows interfaces via ipconfig: {e}")
    
    # If we found interfaces, return them
    if interfaces:
        print(f"[INFO] Detected {len(interfaces)} network interfaces")
        return interfaces
        
    # Fallback to at least provide the default interface
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return [{
            'name': f"Default Interface ({ip_address})",
            'description': f"IP: {ip_address}",
            'guid': 'default',
            'mac': '00:00:00:00:00:00',
            'win_index': 0,
            'scapy_name': None
        }]
    except Exception as e:
        print(f"Error getting default interface: {e}")
        # Last resort fallback
        return [{
            'name': "Default Interface",
            'description': "Default network interface",
            'guid': 'default',
            'mac': '00:00:00:00:00:00',
            'win_index': 0,
            'scapy_name': None
        }]

# Replace scapy's get_windows_if_list with our custom version
scapy.all.get_windows_if_list = custom_get_windows_if_list
import scapy.arch.windows
scapy.arch.windows.get_windows_if_list = custom_get_windows_if_list

# Now it's safe to import NetworkMonitor
from network_Monitoring_Tool import NetworkMonitor, ThreatIntelligence

# Set CustomTkinter appearance
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# Create a wrapper for input function to prevent console input prompts
original_input = input
def silent_input(prompt=""):
    """A version of input() that returns a default value and doesn't wait for user input"""
    print(f"[GUI] Automatic response to prompt: {prompt}")
    # This function is used in the NetworkMonitor initialization before GUI is ready
    # When the interface selection is made via the GUI dropdown, this won't be used
    return "1"  # Always select the first interface during initialization

class NetworkMonitoringGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Monitoring Tool")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.iconbitmap(self.resource_path("network_icon.ico")) if os.path.exists(self.resource_path("network_icon.ico")) else None
        
        # Create a menu bar
        self.create_menu_bar()
        
        # Create a queue for thread-safe communication
        self.log_queue = queue.Queue()
        
        # Save the original print function
        self.original_print = print
        
        # Override the print function in the NetworkMonitor instance
        def custom_print_wrapper(*args, **kwargs):
            # Convert args to string
            message = " ".join(str(arg) for arg in args)
            # Add the message to our queue
            self.log_queue.put(message)
            # Also print to console using the original print
            self.original_print(*args, **kwargs)
        
        # Replace print in the global namespace used by imported modules
        import builtins
        builtins.print = custom_print_wrapper
        
        # Replace input function to prevent console prompts
        builtins.input = silent_input
        
        # Create the Network Monitor instance with GUI mode
        self.network_monitor = self.create_network_monitor()
        
        # Check for Npcap installation
        self.check_npcap_installation()
        
        # Setup the GUI components
        self.create_gui()
        
        # Variables for status updates
        self.monitoring_active = False
        self.update_data_thread = None
        self.thread_running = False
        
        # Start checking for log messages
        self.check_log_queue()
        
    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
        
    def create_gui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section with stats and controls
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill="x", pady=(0, 10))
        
        # Create top section with three columns
        self.create_control_panel()
        
        # Create the tabview for different outputs
        self.create_tabview()
        
        # Create bottom status bar
        self.status_bar = ctk.CTkLabel(
            self.main_frame, 
            text="Status: Ready", 
            anchor="w",
            height=25
        )
        self.status_bar.pack(fill="x", pady=(10, 0))
        
        # Force refresh of interfaces at startup
        self.refresh_interfaces()
    
    def create_control_panel(self):
        # Left column - Network Controls
        self.control_frame = ctk.CTkFrame(self.top_frame)
        self.control_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        control_label = ctk.CTkLabel(self.control_frame, text="Network Controls", font=("Arial", 16, "bold"))
        control_label.pack(pady=10)
        
        # Start/Stop button
        self.start_stop_btn = ctk.CTkButton(
            self.control_frame, 
            text="Start Monitoring",
            command=self.toggle_monitoring
        )
        self.start_stop_btn.pack(pady=5, padx=20, fill="x")
        
        # Interface selection
        interface_frame = ctk.CTkFrame(self.control_frame)
        interface_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(interface_frame, text="Network Interface:").pack(side="left", padx=(0, 10))
        
        # Get the list of interfaces
        self.interfaces = []
        if self.network_monitor.config['interface']:
            for iface in self.network_monitor.config['interface']:
                self.interfaces.append(iface['name'])
        
        self.interface_var = ctk.StringVar(value=self.interfaces[0] if self.interfaces else "No interfaces found")
        self.interface_dropdown = ctk.CTkOptionMenu(
            interface_frame,
            values=self.interfaces,
            variable=self.interface_var,
            command=self.change_interface
        )
        self.interface_dropdown.pack(side="left", fill="x", expand=True)
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            interface_frame,
            text="↻",
            width=30,
            command=self.refresh_interfaces
        )
        self.refresh_btn.pack(side="left", padx=(5, 0))
        
        # Add a "Select All" button for interface selection
        self.select_all_btn = ctk.CTkButton(
            self.control_frame,
            text="Monitor All Interfaces",
            command=self.select_all_interfaces,
            fg_color="#28a745",  # Green color
            hover_color="#218838"
        )
        self.select_all_btn.pack(pady=5, padx=20, fill="x")
        
        # Add Help button
        self.help_btn = ctk.CTkButton(
            self.control_frame,
            text="Help & Usage Guide",
            command=self.show_help_dialog,
            fg_color="#17a2b8",  # Info blue color
            hover_color="#138496"
        )
        self.help_btn.pack(pady=5, padx=20, fill="x")
        
        # Middle column - Configuration
        self.config_frame = ctk.CTkFrame(self.top_frame)
        self.config_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        config_label = ctk.CTkLabel(self.config_frame, text="Threat Detection", font=("Arial", 16, "bold"))
        config_label.pack(pady=10)
        
        # Detection thresholds
        threshold_frame = ctk.CTkFrame(self.config_frame)
        threshold_frame.pack(fill="x", padx=20, pady=5)
        
        # SYN flood threshold
        ctk.CTkLabel(threshold_frame, text="SYN Threshold:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.syn_var = ctk.IntVar(value=self.network_monitor.config['thresholds']['syn'])
        syn_entry = ctk.CTkEntry(threshold_frame, textvariable=self.syn_var, width=50)
        syn_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Port scan threshold
        ctk.CTkLabel(threshold_frame, text="Port Scan Threshold:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.port_var = ctk.IntVar(value=self.network_monitor.config['thresholds']['new_ports'])
        port_entry = ctk.CTkEntry(threshold_frame, textvariable=self.port_var, width=50)
        port_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Apply button
        apply_btn = ctk.CTkButton(
            threshold_frame, 
            text="Apply",
            command=self.update_thresholds
        )
        apply_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Right column - Filtering
        self.filter_frame = ctk.CTkFrame(self.top_frame)
        self.filter_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        filter_label = ctk.CTkLabel(self.filter_frame, text="Filtering Options", font=("Arial", 16, "bold"))
        filter_label.pack(pady=10)
        
        # Subnet filter
        subnet_frame = ctk.CTkFrame(self.filter_frame)
        subnet_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(subnet_frame, text="Subnet Filter (CIDR):").pack(anchor="w", pady=(5, 0))
        
        self.subnet_var = ctk.StringVar(value=self.network_monitor.config['subnet_filter'] or "")
        subnet_entry = ctk.CTkEntry(subnet_frame, textvariable=self.subnet_var)
        subnet_entry.pack(fill="x", pady=5)
        
        # Apply subnet filter button
        apply_subnet_btn = ctk.CTkButton(
            subnet_frame,
            text="Apply Filter",
            command=self.update_subnet_filter
        )
        apply_subnet_btn.pack(pady=5)
        
        # Add custom IP to threat intelligence
        custom_ip_frame = ctk.CTkFrame(self.filter_frame)
        custom_ip_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(custom_ip_frame, text="Add Custom Malicious IP:").pack(anchor="w", pady=(5, 0))
        
        self.custom_ip_var = ctk.StringVar()
        custom_ip_entry = ctk.CTkEntry(custom_ip_frame, textvariable=self.custom_ip_var, placeholder_text="Enter IPv4 or IPv6 address")
        custom_ip_entry.pack(fill="x", pady=5)
        
        # Add IP button
        add_ip_btn = ctk.CTkButton(
            custom_ip_frame,
            text="Add to Threat Database",
            command=self.add_custom_ip,
            fg_color="#dc3545",  # Red for danger
            hover_color="#c82333"
        )
        add_ip_btn.pack(pady=5)
        
        # Display user-added IPs count
        self.user_ips_label = ctk.CTkLabel(
            custom_ip_frame, 
            text=f"User-added IPs: {len(self.network_monitor.threat_intel.user_added_ips)}"
        )
        self.user_ips_label.pack(pady=5)
        
        # Show user IPs button
        show_ips_btn = ctk.CTkButton(
            custom_ip_frame,
            text="Show User-added IPs",
            command=self.show_user_added_ips
        )
        show_ips_btn.pack(pady=5)
        
        # Update threat intel button
        update_threat_btn = ctk.CTkButton(
            self.filter_frame,
            text="Update Threat Intelligence",
            command=self.update_threat_intel
        )
        update_threat_btn.pack(padx=20, pady=10, fill="x")
    
    def create_tabview(self):
        # Create the tabview
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("Live Monitor")
        self.tabview.add("Detected Threats")
        self.tabview.add("Statistics")
        
        # Live Monitor tab
        self.live_text = ctk.CTkTextbox(self.tabview.tab("Live Monitor"), wrap="word")
        self.live_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.live_text.configure(state="disabled")
        
        # Detected Threats tab
        threats_frame = ctk.CTkFrame(self.tabview.tab("Detected Threats"))
        threats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Threats list
        self.threats_text = ctk.CTkTextbox(threats_frame, wrap="word")
        self.threats_text.pack(fill="both", expand=True)
        
        # Add a button to clear threats
        clear_threats_btn = ctk.CTkButton(
            threats_frame,
            text="Clear Threats List",
            command=self.clear_threats
        )
        clear_threats_btn.pack(pady=10)
        
        # Statistics tab
        stats_frame = ctk.CTkFrame(self.tabview.tab("Statistics"))
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add some statistics placeholders
        stats_inner_frame = ctk.CTkFrame(stats_frame)
        stats_inner_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Session info
        self.session_start_label = ctk.CTkLabel(stats_inner_frame, text="Session Start: Not started")
        self.session_start_label.pack(anchor="w", pady=5)
        
        self.session_duration_label = ctk.CTkLabel(stats_inner_frame, text="Session Duration: 00:00:00")
        self.session_duration_label.pack(anchor="w", pady=5)
        
        self.packets_analyzed_label = ctk.CTkLabel(stats_inner_frame, text="Packets Analyzed: 0")
        self.packets_analyzed_label.pack(anchor="w", pady=5)
        
        self.threats_detected_label = ctk.CTkLabel(stats_inner_frame, text="Threats Detected: 0")
        self.threats_detected_label.pack(anchor="w", pady=5)
        
        self.ips_blocked_label = ctk.CTkLabel(stats_inner_frame, text="IPs Blocked: 0")
        self.ips_blocked_label.pack(anchor="w", pady=5)
        
        # Traffic statistics will be added here in the future
    
    def check_log_queue(self):
        """Check for new log messages in the queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.update_live_text(message)
                
                # Also update the threats tab if it's an alert
                if "[!] ALERT:" in message:
                    self.update_threats_text(message)
        except queue.Empty:
            # No more messages in queue, check again after 100ms
            self.root.after(100, self.check_log_queue)
    
    def update_live_text(self, message):
        """Update the live monitor text widget"""
        self.live_text.configure(state="normal")
        self.live_text.insert("end", message + "\n")
        self.live_text.see("end")
        self.live_text.configure(state="disabled")
    
    def update_threats_text(self, message):
        """Update the threats text widget with alert messages"""
        message = message.replace("[!] ALERT: ", "")
        self.threats_text.configure(state="normal")
        self.threats_text.insert("end", message + "\n")
        self.threats_text.see("end")
        self.threats_text.configure(state="disabled")
        
        # Also update the stats
        count = len(self.network_monitor.detected_threats)
        self.threats_detected_label.configure(text=f"Threats Detected: {count}")
    
    def toggle_monitoring(self):
        """Start or stop the monitoring process"""
        if not self.monitoring_active:
            # Start monitoring
            self.monitoring_active = True
            self.start_stop_btn.configure(text="Stop Monitoring", fg_color="#DC3545")
            self.interface_dropdown.configure(state="disabled")
            self.refresh_btn.configure(state="disabled")
            
            # Update session start time
            self.session_start = datetime.datetime.now()
            self.session_start_label.configure(text=f"Session Start: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Start the monitoring thread
            threading.Thread(target=self.monitoring_thread, daemon=True).start()
            
            # Start the stats update thread
            self.thread_running = True
            self.update_data_thread = threading.Thread(target=self.update_statistics, daemon=True)
            self.update_data_thread.start()
            
            self.status_bar.configure(text="Status: Monitoring Active")
        else:
            # Stop monitoring
            self.monitoring_active = False
            self.network_monitor.running = False
            self.start_stop_btn.configure(text="Start Monitoring", fg_color=["#3a7ebf", "#1f538d"])
            self.interface_dropdown.configure(state="normal")
            self.refresh_btn.configure(state="normal")
            
            # Stop the stats thread
            self.thread_running = False
            
            self.status_bar.configure(text="Status: Monitoring Stopped")
    
    def monitoring_thread(self):
        """Thread to run the monitoring process"""
        try:
            if not self.network_monitor.running:
                # Check for Npcap installation
                try:
                    all_interfaces = get_if_list()
                    npf_interfaces = [iface for iface in all_interfaces if iface.startswith(r'\Device\NPF_')]
                    npcap_detected = len(npf_interfaces) > 0
                    
                    if not npcap_detected:
                        self.log_queue.put("[WARNING] No NPF interfaces detected. Using raw socket mode.")
                        self.log_queue.put("[INFO] This mode may have limitations compared to Npcap.")
                    else:
                        self.log_queue.put(f"[INFO] Found {len(npf_interfaces)} NPF interfaces.")
                except Exception as e:
                    self.log_queue.put(f"[WARNING] Error checking for NPF interfaces: {e}")
                
                # Log which interface will be used for monitoring
                if self.network_monitor.config['interface']:
                    if len(self.network_monitor.config['interface']) > 1:
                        self.log_queue.put(f"[INFO] Starting monitoring on {len(self.network_monitor.config['interface'])} interfaces")
                        for iface in self.network_monitor.config['interface'][:3]:  # Show first 3 for brevity
                            self.log_queue.put(f"[INFO] - {iface['name']}")
                        if len(self.network_monitor.config['interface']) > 3:
                            self.log_queue.put(f"[INFO] - (and {len(self.network_monitor.config['interface'])-3} more...)")
                    else:
                        selected_iface = self.network_monitor.config['interface'][0]
                        self.log_queue.put(f"[INFO] Starting monitoring on: {selected_iface['name']}")
                        
                        # Log scapy_name for debugging
                        scapy_name = selected_iface.get('scapy_name')
                        if scapy_name:
                            self.log_queue.put(f"[DEBUG] Using interface: {scapy_name}")
                        else:
                            self.log_queue.put(f"[DEBUG] Using default interface (raw socket mode)")
                else:
                    self.log_queue.put("[ERROR] No interface selected for monitoring")
                    self.monitoring_active = False
                    self.root.after(0, self.reset_ui_after_error)
                    return
                
                # Start monitoring
                try:
                    self.network_monitor.start_monitoring()
                except Exception as e:
                    self.log_queue.put(f"[ERROR] Failed to start monitoring: {str(e)}")
                    
                    # Provide detailed error messages based on the exception
                    if "NpcapNotFoundError" in str(e) or "PacketGetAdapterNames" in str(e):
                        self.log_queue.put("[ERROR] This error typically occurs when Npcap is not installed.")
                        self.log_queue.put("[INFO] Please install Npcap from https://npcap.com/#download")
                    elif "PermissionError" in str(e):
                        self.log_queue.put("[ERROR] Permission denied. Try running the application as Administrator.")
                    elif "socket.error" in str(e) or "error during" in str(e).lower():
                        self.log_queue.put("[ERROR] Socket error. This may be due to interface issues.")
                        self.log_queue.put("[INFO] Try selecting a different interface or check your network configuration.")
                    
                    self.monitoring_active = False
                    self.root.after(0, self.reset_ui_after_error)
                    return
                
                # Keep the monitoring running
                while self.monitoring_active and self.network_monitor.running:
                    time.sleep(0.5)
                
                # Make sure monitoring is stopped
                self.network_monitor.running = False
        except Exception as e:
            self.log_queue.put(f"[!] Error in monitoring thread: {e}")
            import traceback
            self.log_queue.put(traceback.format_exc())
            self.monitoring_active = False
            self.network_monitor.running = False
            
            # Update the UI on the main thread
            self.root.after(0, self.reset_ui_after_error)
    
    def reset_ui_after_error(self):
        """Reset the UI after an error"""
        self.start_stop_btn.configure(text="Start Monitoring", fg_color=["#3a7ebf", "#1f538d"])
        self.interface_dropdown.configure(state="normal")
        self.refresh_btn.configure(state="normal")
        self.status_bar.configure(text="Status: Error Occurred")
    
    def update_statistics(self):
        """Update the statistics in the Stats tab periodically"""
        packets_count = 0
        blocked_ips = 0
        
        while self.thread_running:
            try:
                # Calculate session duration
                if hasattr(self, 'session_start'):
                    duration = datetime.datetime.now() - self.session_start
                    hours, remainder = divmod(duration.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                    self.session_duration_label.configure(text=f"Session Duration: {duration_str}")
                
                # Update packet count (in a real app, you'd get this from your monitoring class)
                packets_count += 10  # Placeholder, replace with real data
                self.packets_analyzed_label.configure(text=f"Packets Analyzed: {packets_count}")
                
                # Update threats count
                threats_count = len(self.network_monitor.detected_threats)
                self.threats_detected_label.configure(text=f"Threats Detected: {threats_count}")
                
                # Update blocked IPs (placeholder)
                # In a real app, you'd track this in your NetworkMonitor class
                self.ips_blocked_label.configure(text=f"IPs Blocked: {blocked_ips}")
                
                time.sleep(1)
            except Exception as e:
                print(f"Error updating statistics: {e}")
                time.sleep(5)  # Wait longer on error
    
    def change_interface(self, interface_name):
        """Handle interface selection change"""
        # Special case for "All Interfaces"
        if interface_name == "All Interfaces" and 'all_interfaces' in self.network_monitor.config:
            # Use all interfaces except the "All Interfaces" option itself
            all_real_interfaces = self.network_monitor.config['all_interfaces'][1:]
            self.network_monitor.config['interface'] = all_real_interfaces
            
            # Update the interface mapping
            self.network_monitor.config['interface_map'] = {
                iface.get('scapy_name', iface['name']): iface['name'] 
                for iface in all_real_interfaces
            }
            
            self.status_bar.configure(text=f"Status: Monitoring all interfaces ({len(all_real_interfaces)})")
            self.log_queue.put(f"[INFO] Selected: All interfaces ({len(all_real_interfaces)})")
            return
        
        # Find the interface in the list
        selected_iface = None
        
        # First check in all_interfaces if it exists
        if 'all_interfaces' in self.network_monitor.config:
            for iface in self.network_monitor.config['all_interfaces']:
                if iface['name'] == interface_name:
                    selected_iface = iface
                    break
        
        # If not found, check in the standard interface list
        if not selected_iface and 'interface' in self.network_monitor.config:
            for iface in self.network_monitor.config['interface']:
                if iface['name'] == interface_name:
                    selected_iface = iface
                    break
        
        if selected_iface:
            # Set the selected interface - IMPORTANT: clear the list and add only the selected interface
            self.network_monitor.config['interface'] = [selected_iface]
            
            # Update the interface mapping for packet analysis
            self.network_monitor.config['interface_map'] = {
                selected_iface.get('scapy_name', selected_iface['name']): selected_iface['name']
            }
            
            # Extract just the interface name without the IP part for display
            display_name = interface_name.split(" (")[0] if " (" in interface_name else interface_name
            
            # Clear any previous status
            if hasattr(self.network_monitor, 'sniffers'):
                self.network_monitor.sniffers = []
            
            self.status_bar.configure(text=f"Status: Interface changed to {display_name}")
            self.log_queue.put(f"[INFO] Selected interface: {display_name}")
            
            # Log more details for debugging
            self.log_queue.put(f"[DEBUG] Interface details: {selected_iface}")
        else:
            self.log_queue.put(f"[ERROR] Interface not found: {interface_name}")
            self.status_bar.configure(text=f"Status: Failed to set interface - not found")
    
    def refresh_interfaces(self):
        """Refresh the list of network interfaces"""
        # First, capture the original interfaces to detect changes
        old_interfaces = set(self.interfaces) if hasattr(self, 'interfaces') else set()
        
        try:
            # Get fresh list of interfaces using our custom function
            if platform.system() == 'Windows':
                windows_interfaces = custom_get_windows_if_list()
                
                # Get all valid interfaces directly - no filtering needed since our custom function already filters
                valid_interfaces = windows_interfaces
                    
                # If no valid interfaces found, try the default interface
                if not valid_interfaces:
                    try:
                        hostname = socket.gethostname()
                        ip_address = socket.gethostbyname(hostname)
                        valid_interfaces = [{
                            'name': f"Default Interface ({ip_address})",
                            'description': f"IP: {ip_address}",
                            'guid': 'default',
                            'scapy_name': None
                        }]
                    except Exception as e:
                        print(f"Error getting default interface: {e}")
                        valid_interfaces = [{
                            'name': "Default Interface",
                            'description': "Default network interface",
                            'guid': 'default',
                            'scapy_name': None
                        }]
                
                # Create a special "All Interfaces" option
                all_interfaces_option = {
                    'name': "All Interfaces",
                    'description': "Monitor all available interfaces",
                    'guid': 'all-interfaces',
                    'scapy_name': None
                }
                
                # Add "All Interfaces" as the first option
                valid_interfaces.insert(0, all_interfaces_option)
                
                # Update the network monitor with all available interfaces
                self.network_monitor.config['all_interfaces'] = valid_interfaces.copy()
                
                # Set the selected interface to the first one for now
                # It will be changed when the user makes a selection
                if valid_interfaces:
                    self.network_monitor.config['interface'] = [valid_interfaces[1]]  # Skip "All Interfaces" for default
                    self.network_monitor.config['interface_map'] = {
                        iface.get('scapy_name', iface['name']): iface['name'] 
                        for iface in valid_interfaces[1:]  # Skip "All Interfaces"
                    }
            else:
                # For Linux, use the built-in method
                self.network_monitor.initialize_network(gui_mode=True)
                self.network_monitor.select_interface_linux()
            
            # Update the dropdown list with the new interfaces
            self.interfaces = []
            if hasattr(self.network_monitor, 'config') and 'all_interfaces' in self.network_monitor.config:
                for iface in self.network_monitor.config['all_interfaces']:
                    self.interfaces.append(iface['name'])
            elif hasattr(self.network_monitor, 'config') and 'interface' in self.network_monitor.config:
                for iface in self.network_monitor.config['interface']:
                    self.interfaces.append(iface['name'])
                    
            # Log the detected interfaces
            if self.interfaces:
                self.log_queue.put(f"[INFO] Available interfaces: {len(self.interfaces)}")
                for i, iface_name in enumerate(self.interfaces, 1):
                    self.log_queue.put(f"  {i}. {iface_name}")
            else:
                self.log_queue.put("[!] No interfaces detected")
                
            # Update the interface dropdown values
            self.interface_dropdown.configure(values=self.interfaces)
            
            # Set the selected interface
            if self.interfaces:
                self.interface_var.set(self.interfaces[0])
                self.interface_dropdown.set(self.interfaces[0])
                
                # Also select this interface in the network monitor
                self.change_interface(self.interfaces[0])
            else:
                self.interface_var.set("No interfaces found")
                self.interface_dropdown.set("No interfaces found")
            
            # Show added/removed interfaces in the status
            new_interfaces = set(self.interfaces)
            added = new_interfaces - old_interfaces
            removed = old_interfaces - new_interfaces
            
            status_msg = f"Status: Found {len(self.interfaces)} interfaces"
            if added and old_interfaces:  # Only show added if we had previous interfaces
                status_msg += f" (Added: {len(added)})"
            if removed:
                status_msg += f" (Removed: {len(removed)})"
                
            self.status_bar.configure(text=status_msg)
        except Exception as e:
            self.log_queue.put(f"[ERROR] Failed to refresh interfaces: {str(e)}")
            import traceback
            self.log_queue.put(traceback.format_exc())
            self.status_bar.configure(text=f"Status: Error refreshing interfaces")
    
    def update_thresholds(self):
        """Update the detection thresholds"""
        try:
            syn_threshold = self.syn_var.get()
            port_threshold = self.port_var.get()
            
            self.network_monitor.config['thresholds']['syn'] = syn_threshold
            self.network_monitor.config['thresholds']['new_ports'] = port_threshold
            
            self.status_bar.configure(text=f"Status: Thresholds updated (SYN: {syn_threshold}, Ports: {port_threshold})")
        except Exception as e:
            self.status_bar.configure(text=f"Status: Error updating thresholds: {e}")
    
    def update_subnet_filter(self):
        """Update the subnet filter"""
        subnet = self.subnet_var.get().strip()
        
        if subnet:
            # Basic validation - you should add more robust validation
            if any(c.isalpha() for c in subnet):
                self.status_bar.configure(text="Status: Invalid subnet format")
                return
            
            self.network_monitor.config['subnet_filter'] = subnet
            self.status_bar.configure(text=f"Status: Subnet filter set to {subnet}")
        else:
            self.network_monitor.config['subnet_filter'] = None
            self.status_bar.configure(text="Status: Subnet filter cleared")
    
    def add_custom_ip(self):
        """Add a custom IP address to the threat intelligence database"""
        ip_address = self.custom_ip_var.get().strip()
        
        if not ip_address:
            self.status_bar.configure(text="Status: Please enter an IP address")
            return
        
        # Try to add the IP
        if self.network_monitor.threat_intel.add_ip(ip_address):
            self.status_bar.configure(text=f"Status: Added {ip_address} to threat database")
            self.custom_ip_var.set("")  # Clear the entry
            # Update the user IPs count label
            self.user_ips_label.configure(text=f"User-added IPs: {len(self.network_monitor.threat_intel.user_added_ips)}")
        else:
            self.status_bar.configure(text=f"Status: Invalid IP address format: {ip_address}")
    
    def show_user_added_ips(self):
        """Show a dialog with all user-added IP addresses"""
        user_ips = self.network_monitor.threat_intel.user_added_ips
        
        # Create a dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("User-added Malicious IPs")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add header
        header_label = ctk.CTkLabel(
            scroll_frame, 
            text=f"User-added IPs ({len(user_ips)})", 
            font=("Arial", 16, "bold")
        )
        header_label.pack(pady=10)
        
        # Add info text
        info_text = "These IPs are considered malicious and will trigger alerts if detected in network traffic."
        info_label = ctk.CTkLabel(
            scroll_frame,
            text=info_text,
            wraplength=450
        )
        info_label.pack(pady=5)
        
        # Add each IP to the list
        if user_ips:
            for ip in sorted(user_ips):
                ip_frame = ctk.CTkFrame(scroll_frame)
                ip_frame.pack(fill="x", pady=2)
                
                ctk.CTkLabel(ip_frame, text=ip, anchor="w").pack(side="left", padx=10)
        else:
            # No IPs message
            ctk.CTkLabel(
                scroll_frame,
                text="No user-added IPs in the database yet.\nUse 'Add Custom Malicious IP' to add addresses.",
                justify="center"
            ).pack(pady=20)
        
        # Add close button
        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100
        ).pack(pady=10)
    
    def update_threat_intel(self):
        """Update the threat intelligence database"""
        self.status_bar.configure(text="Status: Updating threat intelligence...")
        
        # Run this in a separate thread to prevent UI freezing
        def update_thread():
            try:
                original_user_ips = self.network_monitor.threat_intel.user_added_ips.copy()
                self.network_monitor.threat_intel.load_threat_intel()
                
                # Ensure user-added IPs are preserved
                self.network_monitor.threat_intel.user_added_ips = original_user_ips
                self.network_monitor.threat_intel.malicious_ips.update(original_user_ips)
                
                # Update UI on the main thread
                self.root.after(0, lambda: self.status_bar.configure(
                    text=f"Status: Threat intelligence updated ({len(self.network_monitor.threat_intel.malicious_ips)} IPs loaded, {len(original_user_ips)} user-added IPs preserved)"
                ))
                # Update user IPs count
                self.root.after(0, lambda: self.user_ips_label.configure(
                    text=f"User-added IPs: {len(self.network_monitor.threat_intel.user_added_ips)}"
                ))
            except Exception as e:
                # Update UI on the main thread
                self.root.after(0, lambda: self.status_bar.configure(
                    text=f"Status: Error updating threat intelligence: {e}"
                ))
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def clear_threats(self):
        """Clear the threats list"""
        self.network_monitor.detected_threats = []
        self.threats_text.configure(state="normal")
        self.threats_text.delete("1.0", "end")
        self.threats_text.configure(state="disabled")
        self.threats_detected_label.configure(text="Threats Detected: 0")
        self.status_bar.configure(text="Status: Threats list cleared")

    def create_network_monitor(self):
        """Create a network monitor instance that works in GUI mode"""
        nm = NetworkMonitor()
        
        # Initialize with GUI mode flag
        nm.initialize_network(gui_mode=True)
        
        return nm

    def select_all_interfaces(self):
        """Select all available interfaces for monitoring"""
        # Check if we have the all interfaces option in the dropdown
        if "All Interfaces" in self.interfaces:
            self.interface_var.set("All Interfaces")
            self.interface_dropdown.set("All Interfaces")
            self.change_interface("All Interfaces")
        else:
            # If "All Interfaces" is not in the dropdown, select all interfaces manually
            if 'all_interfaces' in self.network_monitor.config:
                # Skip the first one which is the "All Interfaces" option
                all_real_interfaces = self.network_monitor.config['all_interfaces'][1:] 
            else:
                self.refresh_interfaces()  # Refresh to ensure we have the latest interfaces
                all_real_interfaces = self.network_monitor.config.get('interface', [])
                
            if all_real_interfaces:
                self.network_monitor.config['interface'] = all_real_interfaces
                
                # Update the interface mapping
                self.network_monitor.config['interface_map'] = {
                    iface.get('scapy_name', iface['name']): iface['name'] 
                    for iface in all_real_interfaces
                }
                
                self.status_bar.configure(text=f"Status: Monitoring all interfaces ({len(all_real_interfaces)})")
                self.log_queue.put(f"[INFO] Selected: All interfaces ({len(all_real_interfaces)})")
                
                # Update the dropdown to show "All Interfaces"
                if self.interfaces:
                    self.interface_var.set(self.interfaces[0])
                    self.interface_dropdown.set(self.interfaces[0])
            else:
                self.log_queue.put("[ERROR] No interfaces available to monitor")
                self.status_bar.configure(text="Status: No interfaces available")

    def check_npcap_installation(self):
        """Check if Npcap is installed and show a warning if not"""
        # Check for NPF interfaces which indicates Npcap is installed
        try:
            all_interfaces = get_if_list()
            npf_interfaces = [iface for iface in all_interfaces if iface.startswith(r'\Device\NPF_')]
            npcap_detected = len(npf_interfaces) > 0
            
            if not npcap_detected:
                # Show warning in logs
                self.log_queue.put("\n[!] WARNING: Npcap is not installed or not properly configured!")
                self.log_queue.put("[!] This tool requires Npcap to capture network traffic on Windows.")
                self.log_queue.put("[!] Please download and install Npcap from: https://npcap.com/#download")
                self.log_queue.put("[!] After installation, restart this application.")
                self.log_queue.put("[!] Note: Make sure to select 'WinPcap API-compatible Mode' during installation.\n")
                
                # Show a popup warning
                def show_warning():
                    warning_window = ctk.CTkToplevel(self.root)
                    warning_window.title("Npcap Not Detected")
                    warning_window.geometry("500x300")
                    warning_window.transient(self.root)
                    warning_window.grab_set()
                    
                    # Add warning message
                    ctk.CTkLabel(
                        warning_window, 
                        text="Npcap Not Detected", 
                        font=("Arial", 16, "bold")
                    ).pack(pady=(20, 10))
                    
                    message_frame = ctk.CTkFrame(warning_window)
                    message_frame.pack(padx=20, pady=10, fill="both", expand=True)
                    
                    message = (
                        "This tool requires Npcap to capture network traffic on Windows.\n\n"
                        "Without Npcap, the network monitoring functionality will not work correctly.\n\n"
                        "Please download and install Npcap from:\nhttps://npcap.com/#download\n\n"
                        "After installation, restart this application."
                    )
                    
                    ctk.CTkLabel(
                        message_frame,
                        text=message,
                        wraplength=400,
                        justify="left"
                    ).pack(padx=20, pady=20, fill="both", expand=True)
                    
                    # Add download button
                    def open_download_page():
                        import webbrowser
                        webbrowser.open("https://npcap.com/#download")
                        
                    ctk.CTkButton(
                        warning_window,
                        text="Download Npcap",
                        command=open_download_page
                    ).pack(pady=(0, 10))
                    
                    ctk.CTkButton(
                        warning_window,
                        text="Continue Anyway",
                        command=warning_window.destroy
                    ).pack(pady=(0, 20))
                
                # Schedule the warning to appear after the main window is shown
                self.root.after(1000, show_warning)
                
        except Exception as e:
            self.log_queue.put(f"[!] Error checking for Npcap: {e}")

    def show_help_dialog(self):
        """Show help and usage information dialog"""
        help_window = ctk.CTkToplevel(self.root)
        help_window.title("Network Monitoring Tool - Help Guide")
        help_window.geometry("800x600")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Main frame with tabs
        tabview = ctk.CTkTabview(help_window)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        tabview.add("Overview")
        tabview.add("Interface Selection")
        tabview.add("Threat Detection")
        tabview.add("Filtering Options")
        tabview.add("Troubleshooting")
        
        # Overview tab
        overview_frame = ctk.CTkScrollableFrame(tabview.tab("Overview"))
        overview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        overview_text = """
        Network Monitoring Tool
        =======================
        
        This tool monitors your network traffic in real-time, detecting potential security threats such as 
        port scans, SYN floods, and connections from known malicious IP addresses.
        
        Key Features:
        
        • Real-time network traffic monitoring
        • Port scan detection
        • SYN flood detection
        • Malicious IP detection using threat intelligence
        • Support for both IPv4 and IPv6 traffic
        • Custom malicious IP address management
        • Support for multiple network interfaces
        • Network traffic statistics
        
        Getting Started:
        1. Select a network interface from the dropdown menu (or use "Monitor All Interfaces")
        2. Click "Start Monitoring" to begin
        3. View real-time results in the "Live Monitor" tab
        4. Check detected threats in the "Detected Threats" tab
        5. View statistics in the "Statistics" tab
        
        The tool can run in two modes:
        
        1. Npcap Mode (Preferred): Uses Npcap drivers for full packet capture capabilities
        2. Raw Socket Mode (Fallback): Limited functionality but works without Npcap
        
        Requirements:
        • Windows: Npcap recommended, Administrator privileges
        • Linux: Root privileges, libpcap
        """
        
        ctk.CTkLabel(
            overview_frame, 
            text=overview_text.strip(),
            font=("Courier New", 12),
            justify="left",
            wraplength=750
        ).pack(fill="both", expand=True)
        
        # Interface Selection tab
        interface_frame = ctk.CTkScrollableFrame(tabview.tab("Interface Selection"))
        interface_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        interface_text = """
        Interface Selection
        ==================
        
        The "Network Interface" dropdown lets you select which network adapter to monitor:
        
        • Ethernet adapters: Monitor wired network connections
        • WiFi adapters: Monitor wireless network connections
        • VPN adapters: Monitor VPN tunnels
        
        Interfaces are shown with their IP addresses when available: "Ethernet adapter (192.168.1.100)"
        
        Options:
        
        • Dropdown: Select a specific interface to monitor
        • "Monitor All Interfaces" button: Monitor all network interfaces simultaneously
        • Refresh button (↻): Update the list of available interfaces
        
        Tips:
        
        • If you're not sure which interface to choose, use "Monitor All Interfaces"
        • For best performance on a busy network, select only the interface you want to monitor
        • If you have multiple network adapters (e.g., WiFi and Ethernet), monitor the one you're actively using
        • VPN interfaces may show different traffic than physical adapters
        
        When an interface is selected, the tool will display:
        • [INFO] Selected interface: (interface name)
        • [INFO] Starting monitoring on: (interface name)
        
        If you experience issues with a particular interface, try selecting a different one or use the "Monitor All Interfaces" option.
        """
        
        ctk.CTkLabel(
            interface_frame, 
            text=interface_text.strip(),
            font=("Courier New", 12),
            justify="left",
            wraplength=750
        ).pack(fill="both", expand=True)
        
        # Threat Detection tab
        threat_frame = ctk.CTkScrollableFrame(tabview.tab("Threat Detection"))
        threat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        threat_text = """
        Threat Detection
        ===============
        
        The tool detects several types of network security threats on both IPv4 and IPv6:
        
        1. Port Scans:
            • What it is: An attempt to find open ports on your system
            • Detection: Multiple new ports accessed from a single IP address
            • Threshold: Set in "Port Scan Threshold" (default: 3 ports/minute)
            • Alert: "[ALERT] Port scan from X.X.X.X (IPv4/6) to TCP/UDP port XXX"
        
        2. SYN Floods:
            • What it is: A denial-of-service attack overwhelming a server with SYN packets
            • Detection: Excessive SYN packets from a single IP address
            • Threshold: Set in "SYN Threshold" (default: 5 SYN packets/minute)
            • Alert: "[ALERT] SYN flood from X.X.X.X (IPv4/6) to port XXX"
        
        3. Malicious IP Connections:
            • What it is: Traffic from known malicious IP addresses
            • Detection: Matching against threat intelligence database
            • Alert: "[ALERT] Malicious TCP/UDP traffic from X.X.X.X (IPv4/6) to port XXX"
        
        Adjusting Thresholds:
        
        • Increase thresholds if you get too many false positives
        • Decrease thresholds for more sensitive detection
        • Click "Apply" after changing threshold values
        
        All detected threats are logged in the "Detected Threats" tab. You can clear this list using the "Clear Threats List" button.
        """
        
        ctk.CTkLabel(
            threat_frame, 
            text=threat_text.strip(),
            font=("Courier New", 12),
            justify="left",
            wraplength=750
        ).pack(fill="both", expand=True)
        
        # Filtering Options tab
        filtering_frame = ctk.CTkScrollableFrame(tabview.tab("Filtering Options"))
        filtering_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        filtering_text = """
        Filtering Options
        ================
        
        Subnet Filter:
        
        • Purpose: Focus monitoring on specific network segments
        • Format: CIDR notation (e.g., 192.168.1.0/24 or 2001:db8::/64)
        • Examples:
          - 192.168.1.0/24: Monitor only the 192.168.1.x IPv4 subnet
          - 10.0.0.0/8: Monitor the entire 10.x.x.x private network range
          - 2001:db8::/64: Monitor a specific IPv6 subnet
          - 0.0.0.0/0: Monitor all traffic (default)
        
        • Usage:
          1. Enter the CIDR subnet in the "Subnet Filter" field
          2. Click "Apply Filter"
          3. Start monitoring
        
        Custom Malicious IP Management:
        
        • Purpose: Add your own known malicious IP addresses to the threat database
        • Supports: Both IPv4 (e.g., 8.8.8.8) and IPv6 (e.g., 2001:4860:4860::8888) addresses
        
        • Usage:
          1. Enter the IP address in the "Add Custom Malicious IP" field
          2. Click "Add to Threat Database"
          3. The IP will be saved in user_added_ips.txt and preserved during updates
        
        • View Your Custom IPs:
          - Click "Show User-added IPs" to see all IP addresses you've added
          - These IPs will trigger alerts if seen in network traffic
          - Your custom IPs are preserved even when updating the threat intelligence database
        
        Threat Intelligence:
        
        • Purpose: Update the database of known malicious IP addresses
        • Source: Uses the Emerging Threats compromised IPs list
        • Usage: Click "Update Threat Intelligence" to refresh the database
        • User-added IPs are always preserved during updates
        
        Note: The threat intelligence database is stored in "malicious_ips.txt" and user-added IPs are stored in "user_added_ips.txt".
        """
        
        ctk.CTkLabel(
            filtering_frame, 
            text=filtering_text.strip(),
            font=("Courier New", 12),
            justify="left",
            wraplength=750
        ).pack(fill="both", expand=True)
        
        # Troubleshooting tab
        troubleshooting_frame = ctk.CTkScrollableFrame(tabview.tab("Troubleshooting"))
        troubleshooting_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        troubleshooting_text = """
        Troubleshooting
        ==============
        
        Common Issues:
        
        1. "No valid sniffing interfaces found!"
            • Solution:
              • Make sure Npcap is installed: https://npcap.com/#download
              • Run the application as Administrator
              • The tool will automatically fall back to raw socket mode
        
        2. Interface selection issues
            • Solutions:
              • Click the Refresh button (↻) to reload interfaces
              • Try using the "Monitor All Interfaces" button
              • Select a different interface from the dropdown
              • Look for interfaces that show an IP address in parentheses
        
        3. Error starting monitoring
            • Solutions:
              • Verify Npcap is properly installed (Windows)
              • Make sure you're running with administrator privileges
              • Disable any VPN software temporarily
              • Check that the selected interface is connected and active
        
        4. Missing or incomplete packet data
            • Solutions:
              • Make sure you're running in Npcap mode (not raw socket mode)
              • Try selecting a different interface
              • Check for any firewall rules blocking packet capture
        
        5. No traffic shown in Live Monitor
            • Solutions: 
              • Make sure you've selected the right interface
              • Generate some network traffic (open a website, etc.)
              • Check if any firewall/security software is blocking the application
        
        For Windows users, Npcap is recommended for best performance. To install:
        
        1. Download Npcap from: https://npcap.com/#download
        2. Run the installer as Administrator
        3. Select "Install Npcap in WinPcap API-compatible Mode"
        4. Restart your computer
        5. Run the Network Monitoring Tool as Administrator
        """
        
        ctk.CTkLabel(
            troubleshooting_frame, 
            text=troubleshooting_text.strip(),
            font=("Courier New", 12),
            justify="left",
            wraplength=750
        ).pack(fill="both", expand=True)
        
        # Close button at the bottom
        ctk.CTkButton(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=100
        ).pack(pady=10)

    def create_menu_bar(self):
        """Create the application menu bar"""
        # Create the menu bar
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Start Monitoring", command=lambda: self.toggle_monitoring() if not self.monitoring_active else None)
        file_menu.add_command(label="Stop Monitoring", command=lambda: self.toggle_monitoring() if self.monitoring_active else None)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Interface Menu
        interface_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Interface", menu=interface_menu)
        interface_menu.add_command(label="Refresh Interfaces", command=self.refresh_interfaces)
        interface_menu.add_command(label="Monitor All Interfaces", command=self.select_all_interfaces)
        
        # Tools Menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Update Threat Intelligence", command=self.update_threat_intel)
        tools_menu.add_command(label="Clear Threats List", command=self.clear_threats)
        
        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Usage Guide", command=self.show_help_dialog)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def show_about_dialog(self):
        """Show about dialog with version and author information"""
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("About Network Monitoring Tool")
        about_window.geometry("400x300")
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Title
        ctk.CTkLabel(
            about_window, 
            text="Network Monitoring Tool",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 5))
        
        # Version
        ctk.CTkLabel(
            about_window, 
            text="Version 1.0.0"
        ).pack(pady=5)
        
        # Description
        ctk.CTkLabel(
            about_window, 
            text="A real-time network monitoring tool for\ndetecting potential security threats.",
            font=("Arial", 12),
            justify="center"
        ).pack(pady=10)
        
        # Requirements
        ctk.CTkLabel(
            about_window, 
            text="Requires Python 3.8+, Scapy, and Npcap (Windows)",
            font=("Arial", 10),
            justify="center"
        ).pack(pady=5)
        
        # License
        ctk.CTkLabel(
            about_window, 
            text="Open Source - MIT License",
            font=("Arial", 10),
            justify="center"
        ).pack(pady=5)
        
        # Links
        link_frame = ctk.CTkFrame(about_window)
        link_frame.pack(pady=10)
        
        def open_npcap():
            import webbrowser
            webbrowser.open("https://npcap.com/#download")
        
        ctk.CTkButton(
            link_frame,
            text="Download Npcap",
            command=open_npcap,
            width=150
        ).pack(pady=5)
        
        # Close button
        ctk.CTkButton(
            about_window,
            text="Close",
            command=about_window.destroy,
            width=100
        ).pack(pady=15)

def main():
    try:
        # Fix for scapy sniffing when we have a None interface (use default)
        original_sniff = sniff
        def patched_sniff(*args, **kwargs):
            # If iface is None, remove it from kwargs to use default interface
            if 'iface' in kwargs and kwargs['iface'] is None:
                print("[INFO] Using default interface for packet capture")
                del kwargs['iface']
            return original_sniff(*args, **kwargs)
        
        # Replace sniff function with our patched version
        scapy.all.sniff = patched_sniff
        
        # Create and run the GUI
        root = ctk.CTk()
        app = NetworkMonitoringGUI(root)
        root.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), sys.exit(0)))
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 