import threading
from scapy.all import sniff, TCP, IP, UDP, get_if_list, conf
from scapy.arch.windows import get_windows_if_list
import datetime
import time
import requests
import sys
import platform
import os
from pathlib import Path
from collections import defaultdict
import warnings
import ctypes
import signal
import scapy.layers.inet6

warnings.filterwarnings("ignore", category=UserWarning)

if platform.system() == 'Windows':
    conf.use_npcap = True

class ThreatIntelligence:
    def __init__(self):
        self.malicious_ips = set()
        self.user_added_ips = set()
        self.load_threat_intel()
        self.load_user_added_ips()

    def load_threat_intel(self):
        """Load the threat intelligence data from the malicious_ips.txt file or download it"""
        threat_file = Path("malicious_ips.txt")
        try:
            if not threat_file.exists():
                print("[*] Downloading threat intelligence database...")
                try:
                    response = requests.get("https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
                                        timeout=10)
                    threat_file.write_text(response.text)
                    print(f"[+] Downloaded {len(response.text.splitlines())} IP addresses")
                except Exception as e:
                    print(f"[!] Download failed: {e}")
                    print("[*] Creating empty threat intelligence file")
                    threat_file.write_text("")
            
            # Load the malicious IPs from the file
            with open(threat_file, 'r') as f:
                self.malicious_ips = {line.strip() for line in f if line.strip() and not line.startswith('#')}
                
            print(f"[+] Loaded {len(self.malicious_ips)} IPs from threat intelligence database")
                
        except Exception as e:
            print(f"[!] Threat intelligence error: {e}")
            self.malicious_ips = set()
    
    def load_user_added_ips(self):
        """Load user-added IP addresses from user_added_ips.txt"""
        user_file = Path("user_added_ips.txt")
        try:
            if not user_file.exists():
                print("[*] Creating user-added IPs file")
                user_file.write_text("")
                
            # Load user-added IPs
            with open(user_file, 'r') as f:
                self.user_added_ips = {line.strip() for line in f if line.strip() and not line.startswith('#')}
                
            print(f"[+] Loaded {len(self.user_added_ips)} user-added IPs")
            
            # Add user IPs to the malicious set
            self.malicious_ips.update(self.user_added_ips)
            
        except Exception as e:
            print(f"[!] Error loading user-added IPs: {e}")
            self.user_added_ips = set()
    
    def add_ip(self, ip_address):
        """Add a user-specified IP address to the user_added_ips.txt file"""
        # Validate the IP address (IPv4 or IPv6)
        if not self.is_valid_ip(ip_address):
            print(f"[!] Invalid IP address format: {ip_address}")
            return False
            
        try:
            # Add to the set
            self.user_added_ips.add(ip_address)
            self.malicious_ips.add(ip_address)
            
            # Save to the file
            user_file = Path("user_added_ips.txt")
            with open(user_file, 'w') as f:
                for ip in sorted(self.user_added_ips):
                    f.write(f"{ip}\n")
                    
            print(f"[+] Added {ip_address} to user-added IPs")
            return True
            
        except Exception as e:
            print(f"[!] Error adding IP: {e}")
            return False
    
    def is_valid_ip(self, ip_address):
        """Validate an IP address (IPv4 or IPv6)"""
        try:
            import ipaddress
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    def check_ip(self, ip_address):
        """Check if an IP address is in the threat intelligence database"""
        return ip_address in self.malicious_ips

class NetworkMonitor:
    def __init__(self):
        self.running = False
        self.config = {
            'thresholds': {
                'syn': 5,
                'new_ports': 3,
                'malicious': 1
            },
            'subnet_filter': None,
            'interface': [],
            'interface_map': {}
        }
        self.threat_intel = ThreatIntelligence()
        self.counters = defaultdict(lambda: defaultdict(int))
        self.known_ports = defaultdict(set)
        self.detected_threats = []
        self.sniffers = []
        signal.signal(signal.SIGINT, self.signal_handler)
        self.initialize_network()

    def signal_handler(self, sig, frame):
        if self.running:
            self.running = False
            print("\n[+] Monitoring stopped by user")
        else:
            print("\n[+] Exiting...")
            sys.exit(0)

    def initialize_network(self, gui_mode=False):
        if platform.system() == 'Windows':
            self.verify_admin_windows()
            self.gui_mode = gui_mode  # Store the gui_mode setting
            if not gui_mode:
                self.select_interface_windows()
        else:
            self.verify_admin_linux()
            self.gui_mode = gui_mode  # Store the gui_mode setting
            if not gui_mode:
                self.select_interface_linux()

    def verify_admin_windows(self):
        try:
            if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                print("[!] Requires Administrator privileges on Windows")
                sys.exit(1)
        except AttributeError:
            pass

    def verify_admin_linux(self):
        if os.geteuid() != 0:
            print("[!] Requires root privileges on Linux")
            sys.exit(1)

    def select_interface_windows(self):
        scapy_ifaces = []
        
        # Check if Npcap is properly installed
        try:
            print("[DEBUG] Checking for Npcap installation...")
            scapy_ifaces = get_if_list()
            print(f"[DEBUG] Raw interfaces from scapy: {scapy_ifaces}")
            
            # Check if any NPF interfaces exist
            npf_interfaces = [iface for iface in scapy_ifaces if iface.startswith(r'\Device\NPF_')]
            print(f"[DEBUG] NPF interfaces found: {len(npf_interfaces)}")
            if npf_interfaces:
                print(f"[DEBUG] First few NPF interfaces: {npf_interfaces[:3]}")
            
            npcap_installed = any(iface.startswith(r'\Device\NPF_') for iface in scapy_ifaces)
            print(f"[DEBUG] Npcap installed detection result: {npcap_installed}")
        except Exception as e:
            print(f"[DEBUG] Error when getting interfaces from scapy: {e}")
            npcap_installed = False
        
        if not npcap_installed:
            print("\n[!] ERROR: Npcap is not installed or not working properly!")
            print("[!] This tool requires Npcap to capture network traffic on Windows.")
            print("[!] Please download and install Npcap from: https://npcap.com/#download")
            print("[!] After installation, restart this application.")
            print("\n[!] Note: Make sure to select 'WinPcap API-compatible Mode' during installation.")
            
            # In GUI mode, we'll continue with a fallback but show warning
            if not hasattr(self, 'gui_mode') or not self.gui_mode:
                sys.exit(1)

        # Extract GUIDs from Scapy interface names
        valid_guids = set()
        for iface in scapy_ifaces:
            if iface.startswith(r'\Device\NPF_'):
                guid_part = iface.split('_')[-1].strip('{}')
                valid_guids.add(guid_part.lower())
        
        print(f"[DEBUG] Valid GUIDs extracted: {len(valid_guids)}")
        if valid_guids:
            print(f"[DEBUG] Example GUIDs: {list(valid_guids)[:3]}")

        # Try to get Windows interfaces directly
        try:
            print("[DEBUG] Getting Windows interface list...")
            windows_if_list = get_windows_if_list()
            print(f"[DEBUG] Windows interfaces count: {len(windows_if_list)}")
            for idx, iface in enumerate(windows_if_list[:3]):
                print(f"[DEBUG] Interface {idx}: Name={iface.get('name')}, GUID={iface.get('guid')}")
        except Exception as e:
            print(f"[DEBUG] Error when getting Windows interface list: {e}")
            windows_if_list = []

        valid_interfaces = []
        try:
            for iface in get_windows_if_list():
                iface_guid = iface.get('guid', '').strip('{}').lower()
                print(f"[DEBUG] Checking interface '{iface.get('name')}' with GUID '{iface_guid}'")
                
                # Check if this guid is in our valid_guids set
                if iface_guid in valid_guids:
                    print(f"[DEBUG] - GUID match found")
                    if 'loopback' not in iface['name'].lower():
                        print(f"[DEBUG] - Not a loopback, adding to valid interfaces")
                        valid_interfaces.append({
                            'name': iface['name'],
                            'guid': iface['guid'],
                            'scapy_name': f"\\Device\\NPF_{iface['guid']}",
                            'description': iface.get('description', 'No description available')
                        })
                    else:
                        print(f"[DEBUG] - Skipping loopback interface")
                else:
                    print(f"[DEBUG] - No GUID match")
        except Exception as e:
            print(f"[!] Error when getting interface list: {e}")

        print(f"[DEBUG] Valid interfaces found: {len(valid_interfaces)}")
        for idx, iface in enumerate(valid_interfaces):
            print(f"[DEBUG] Valid interface {idx}: {iface['name']} - {iface['description']}")

        # Alternative approach - use all network adapters, not just NPF ones
        if not valid_interfaces:
            print("[!] No valid sniffing interfaces found via NPF devices!")
            print("[!] Trying alternative approach with raw sockets...")
            
            try:
                # Try to get all physical network adapters from Windows
                import socket
                import psutil  # Make sure psutil is in requirements.txt
                
                # Get all network interfaces using psutil
                net_if_stats = psutil.net_if_stats()
                net_if_addrs = psutil.net_if_addrs()
                
                print(f"[DEBUG] Found {len(net_if_stats)} interfaces with psutil")
                
                for nic_name, nic_stats in net_if_stats.items():
                    # Skip loopback interfaces
                    if 'loopback' in nic_name.lower():
                        continue
                        
                    # Only include interfaces that are up
                    if nic_stats.isup:
                        ip_address = None
                        
                        # Try to get an IPv4 address
                        if nic_name in net_if_addrs:
                            for addr in net_if_addrs[nic_name]:
                                if addr.family == socket.AF_INET:
                                    ip_address = addr.address
                                    break
                        
                        display_name = f"{nic_name}"
                        if ip_address:
                            display_name += f" ({ip_address})"
                            
                        valid_interfaces.append({
                            'name': display_name,
                            'guid': f"raw-{nic_name}",
                            'scapy_name': None,  # Use system default
                            'description': f"Speed: {nic_stats.speed} Mbps, MTU: {nic_stats.mtu}"
                        })
                        print(f"[DEBUG] Added alternative interface: {display_name}")
            except ImportError:
                print("[DEBUG] psutil not installed, trying basic socket approach")
            except Exception as e:
                print(f"[DEBUG] Error finding alternative interfaces: {e}")

        if not valid_interfaces:
            print("[!] No valid sniffing interfaces found!")
            
            if not npcap_installed:
                print("[!] This is likely because Npcap is not installed or not configured properly.")
                print("[!] Please install Npcap from: https://npcap.com/#download")
            else:
                print("[!] This could be due to network interface issues or permission problems.")
                print("[!] Try running the application as Administrator.")
                
                # Additional troubleshooting for when Npcap is installed but no interfaces found
                print("\n[DEBUG] Additional troubleshooting:")
                print("[DEBUG] 1. Try reinstalling Npcap with the 'WinPcap API-compatible Mode' option checked")
                print("[DEBUG] 2. Ensure your network adapters are enabled in Windows")
                print("[DEBUG] 3. Check Windows Device Manager for any network adapter issues")
                print("[DEBUG] 4. Make sure Windows Firewall is not blocking the application")
                print("[DEBUG] 5. Try running as Administrator with UAC disabled temporarily")
            
            # Add a default interface instead of exiting
            try:
                import socket
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                valid_interfaces = [{
                    'name': f"Default Interface ({ip_address})",
                    'guid': 'default',
                    'scapy_name': None,  # None will use default interface
                    'description': f"IP: {ip_address}"
                }]
            except Exception:
                # Very basic fallback
                valid_interfaces = [{
                    'name': "Default Interface",
                    'guid': 'default',
                    'scapy_name': None,
                    'description': "Default network interface"
                }]

        # If we're in GUI mode, just select all interfaces
        if hasattr(self, 'gui_mode') and self.gui_mode:
            self.config['interface'] = valid_interfaces
            self.config['interface_map'] = {iface.get('scapy_name', iface['name']): iface['name'] 
                                          for iface in valid_interfaces}
            return

        print("\nAvailable Interfaces:")
        for idx, iface in enumerate(valid_interfaces, 1):
            print(f"{idx}. {iface['name']} - {iface['description']}")

        while True:
            choice = input("\nSelect interface number or type 'All': ").strip().lower()
            if choice == 'all':
                self.config['interface'] = valid_interfaces
                self.config['interface_map'] = {iface.get('scapy_name', iface['name']): iface['name'] 
                                              for iface in valid_interfaces}
                return
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(valid_interfaces):
                    self.config['interface'] = [valid_interfaces[choice_idx]]
                    self.config['interface_map'] = {
                        valid_interfaces[choice_idx].get('scapy_name', valid_interfaces[choice_idx]['name']): 
                        valid_interfaces[choice_idx]['name']
                    }
                    return
                print("Invalid selection")
            except ValueError:
                print("Please enter a valid number or 'All'")

    def select_interface_linux(self):
        scapy_ifaces = get_if_list()

        print("\nAvailable Interfaces:")
        for idx, iface in enumerate(scapy_ifaces, 1):
            print(f"{idx}. {iface}")

        while True:
            choice = input("\nSelect interface number or type 'All': ").strip().lower()
            if choice == 'all':
                self.config['interface'] = [{'name': iface, 'scapy_name': iface} for iface in scapy_ifaces]
                return
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(scapy_ifaces):
                    selected_iface = scapy_ifaces[choice_idx]
                    self.config['interface'] = [{'name': selected_iface, 'scapy_name': selected_iface}]
                    return
                print("Invalid selection")
            except ValueError:
                print("Please enter a valid number or 'All'")

    def packet_analyzer(self, packet, iface_name):
        if not packet.haslayer(IP) and not packet.haslayer(scapy.layers.inet6.IPv6):
            return

        # Extract the source IP - handle both IPv4 and IPv6
        if packet.haslayer(IP):
            src_ip = packet[IP].src
            ip_version = 4
        elif packet.haslayer(scapy.layers.inet6.IPv6):
            src_ip = packet[scapy.layers.inet6.IPv6].src
            ip_version = 6
        else:
            return  # Shouldn't happen due to the check above, but just in case

        dst_port = None
        protocol = None

        # Handle TCP and UDP for both IPv4 and IPv6
        if packet.haslayer(TCP):
            dst_port = packet[TCP].dport
            protocol = 'TCP'
        elif packet.haslayer(UDP):
            dst_port = packet[UDP].dport
            protocol = 'UDP'
        else:
            return

        # Check if source IP is in threat intelligence database
        if src_ip in self.threat_intel.malicious_ips:
            self.trigger_alert(
                f"Malicious {protocol} traffic from {src_ip} (IPv{ip_version}) to port {dst_port} on {iface_name}", 
                'malicious'
            )

        # Check for SYN flood (TCP only)
        if protocol == 'TCP' and packet[TCP].flags & 0x02:
            self.counters[src_ip]['syn'] += 1
            if self.counters[src_ip]['syn'] > self.config['thresholds']['syn']:
                self.trigger_alert(
                    f"SYN flood from {src_ip} (IPv{ip_version}) to port {dst_port} on {iface_name}", 
                    'syn'
                )

        # Check for port scanning
        if dst_port not in self.known_ports[src_ip]:
            self.known_ports[src_ip].add(dst_port)
            self.counters[src_ip]['new_ports'] += 1
            if self.counters[src_ip]['new_ports'] > self.config['thresholds']['new_ports']:
                self.trigger_alert(
                    f"Port scan from {src_ip} (IPv{ip_version}) to {protocol} port {dst_port} on {iface_name}", 
                    'scan'
                )

    def trigger_alert(self, message, alert_type):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_entry = f"[{timestamp}] {message}"
        self.detected_threats.append(alert_entry)
        print(f"\n[!] ALERT: {alert_entry}")
        
        if alert_type == 'malicious':
            self.block_ip(message.split()[-6])  # Extract IP from message

    def block_ip(self, ip_address):
        if platform.system() == 'Windows':
            try:
                os.system(f'netsh advfirewall firewall add rule name="Block {ip_address}" '
                          f'dir=in action=block remoteip={ip_address}')
                print(f"Blocked {ip_address} in Windows Firewall")
            except Exception as e:
                print(f"Failed to block IP: {e}")
        elif platform.system() == 'Linux':
            try:
                os.system(f'iptables -A INPUT -s {ip_address} -j DROP')
                print(f"Blocked {ip_address} using iptables")
            except Exception as e:
                print(f"Failed to block IP: {e}")

    def start_monitoring(self):
        self.detected_threats = []
        if not self.threat_intel.malicious_ips:
            print("[!] No threat intelligence loaded - continuing with basic monitoring")

        # If no interfaces are selected, use a default one
        if not self.config['interface']:
            print("[!] No interfaces selected, using default interface")
            try:
                import socket
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                self.config['interface'] = [{
                    'name': f"Default Interface ({ip_address})",
                    'description': f"IP: {ip_address}",
                    'guid': 'default',
                    'scapy_name': None  # None will use default interface
                }]
            except Exception:
                self.config['interface'] = [{
                    'name': "Default Interface",
                    'description': "Default network interface",
                    'guid': 'default',
                    'scapy_name': None
                }]

        print(f"\n[+] Starting monitoring on {len(self.config['interface'])} interface(s)...")
        self.running = True

        # Stop any existing sniffers
        self.sniffers = []

        def sniff_target(iface_info):
            try:
                iface_name = iface_info.get('name', 'Default Interface')
                scapy_name = iface_info.get('scapy_name')
                
                print(f"[+] Starting capture on {iface_name}")
                
                # Build the filter expression
                filter_expr = 'tcp or udp'
                if self.config['subnet_filter']:
                    filter_expr += f" and net {self.config['subnet_filter']}"
                
                # Try to use the specific interface if provided
                try:
                    if scapy_name:
                        print(f"[DEBUG] Using interface: {scapy_name}")
                        sniff(
                            filter=filter_expr,
                            prn=lambda p: self.packet_analyzer(p, iface_name),
                            store=False,
                            stop_filter=lambda _: not self.running,
                            iface=scapy_name
                        )
                    else:
                        # If no specific interface, use default (raw sockets mode)
                        print(f"[DEBUG] Using default interface (raw socket mode)")
                        sniff(
                            filter=filter_expr,
                            prn=lambda p: self.packet_analyzer(p, iface_name),
                            store=False,
                            stop_filter=lambda _: not self.running
                        )
                except Exception as e:
                    print(f"[!] Error with interface {iface_name} using Scapy: {str(e)}")
                    print("[!] Trying alternative capture method...")
                    
                    # Fall back to raw socket capture if NPF interface fails
                    try:
                        sniff(
                            filter=filter_expr,
                            prn=lambda p: self.packet_analyzer(p, iface_name),
                            store=False,
                            stop_filter=lambda _: not self.running
                        )
                    except Exception as fallback_error:
                        print(f"[!] Alternative capture also failed: {fallback_error}")
                        raise  # Re-raise the error to be caught by the outer exception handler
                
            except PermissionError:
                print(f"[!] Permission denied for interface {iface_info.get('name', 'Unknown')}")
                print("[!] Try running the application as Administrator")
            except Exception as e:
                print(f"[!] Interface {iface_info.get('name', 'Unknown')} error: {str(e)}")
                
                # Provide more helpful error messages
                if "NpcapNotFoundError" in str(e) or "PacketGetAdapterNames" in str(e):
                    print("[!] This error typically occurs when Npcap is not installed.")
                    print("[!] Please install Npcap from https://npcap.com/#download")
                elif "socket.error" in str(e) or "No such device" in str(e):
                    print("[!] Socket error. This may be due to interface issues.")
                    print("[!] Try selecting a different interface.")
            finally:
                if self.running:
                    print(f"[!] Sniffer for {iface_info.get('name', 'Unknown')} stopped unexpectedly")

        for iface in self.config['interface']:
            thread = threading.Thread(target=sniff_target, args=(iface,))
            thread.daemon = True
            thread.start()
            self.sniffers.append(thread)

    def show_menu(self):
        while True:
            print("\n=== Network Monitoring Console ===")
            print("1. Start/Stop Monitoring")
            print("2. Change Interface")
            print("3. Configure Detection Thresholds")
            print("4. Set Subnet Filter")
            print("5. View Detected Threats")
            print("6. Update Threat Intelligence")
            print("7. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == '1':
                self.toggle_monitoring()
            elif choice == '2':
                if self.running:
                    print("[!] Stop monitoring before changing interface.")
                else:
                    if platform.system() == 'Linux':
                        self.select_interface_linux()
                    elif platform.system() == 'Windows':
                        self.select_interface_windows()
            elif choice == '3':
                self.configure_thresholds()
            elif choice == '4':
                self.set_subnet_filter()
            elif choice == '5':
                self.show_threats()
            elif choice == '6':
                self.threat_intel.load_threat_intel()
                print("[+] Threat intelligence updated")
            elif choice == '7':
                self.running = False
                print("[+] Exiting...")
                sys.exit(0)
            else:
                print("[!] Invalid option")

    def toggle_monitoring(self):
        if self.running:
            self.running = False
            print("[+] Monitoring stopped")
        else:
            self.start_monitoring()
            print("[+] Monitoring started. Press Ctrl+C to stop.")
            try:
                while self.running:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                self.running = False
                print("\n[+] Monitoring stopped by user")

    def configure_thresholds(self):
        print("\n--- Threat Detection Thresholds ---")
        self.config['thresholds']['syn'] = int(
            input(f"SYN packets/min ({self.config['thresholds']['syn']}): ") 
            or self.config['thresholds']['syn']
        )
        self.config['thresholds']['new_ports'] = int(
            input(f"New ports/min ({self.config['thresholds']['new_ports']}): ") 
            or self.config['thresholds']['new_ports']
        )
        print("[+] Thresholds updated")

    def set_subnet_filter(self):
        subnet = input("\nEnter subnet filter (CIDR format): ")
        if any(c.isalpha() for c in subnet):
            print("[!] Invalid subnet format")
            return
        self.config['subnet_filter'] = subnet or None
        print("[+] Filter updated")

    def show_threats(self):
        print("\n=== Detected Security Events ===")
        if not self.detected_threats:
            print("No threats detected in current session")
        for threat in self.detected_threats:
            print(threat)
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        NetworkMonitor().show_menu()
    except KeyboardInterrupt:
        print("\n[+] Exiting...")
        sys.exit(0)