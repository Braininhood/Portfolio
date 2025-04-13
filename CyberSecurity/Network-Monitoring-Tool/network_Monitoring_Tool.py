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

warnings.filterwarnings("ignore", category=UserWarning)

if platform.system() == 'Windows':
    conf.use_npcap = True

class ThreatIntelligence:
    def __init__(self):
        self.malicious_ips = set()
        self.load_threat_intel()

    def load_threat_intel(self):
        threat_file = Path("malicious_ips.txt")
        try:
            if not threat_file.exists():
                response = requests.get("https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
                                        timeout=10)
                threat_file.write_text(response.text)
            
            with open(threat_file, 'r') as f:
                self.malicious_ips = {line.strip() for line in f if line.strip() and not line.startswith('#')}
                
        except Exception as e:
            print(f"[!] Threat intelligence error: {e}")
            self.malicious_ips = set()

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

    def initialize_network(self):
        if platform.system() == 'Windows':
            self.verify_admin_windows()
            self.select_interface_windows()
        else:
            self.verify_admin_linux()
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
        scapy_ifaces = get_if_list()

        # Extract GUIDs from Scapy interface names
        valid_guids = set()
        for iface in scapy_ifaces:
            if iface.startswith(r'\Device\NPF_'):
                guid_part = iface.split('_')[-1].strip('{}')
                valid_guids.add(guid_part.lower())

        valid_interfaces = []
        for iface in get_windows_if_list():
            iface_guid = iface.get('guid', '').strip('{}').lower()
            if iface_guid in valid_guids and 'loopback' not in iface['name'].lower():
                valid_interfaces.append({
                    'name': iface['name'],
                    'guid': iface['guid'],
                    'scapy_name': f"\\Device\\NPF_{iface['guid']}",
                    'description': iface.get('description', 'No description available')
                })

        if not valid_interfaces:
            print("[!] No valid sniffing interfaces found!")
            sys.exit(1)

        print("\nAvailable Interfaces:")
        for idx, iface in enumerate(valid_interfaces, 1):
            print(f"{idx}. {iface['name']} - {iface['description']}")

        while True:
            choice = input("\nSelect interface number or type 'All': ").strip().lower()
            if choice == 'all':
                self.config['interface'] = valid_interfaces
                self.config['interface_map'] = {iface['scapy_name']: iface['name'] 
                                              for iface in valid_interfaces}
                return
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(valid_interfaces):
                    self.config['interface'] = [valid_interfaces[choice_idx]]
                    self.config['interface_map'] = {
                        valid_interfaces[choice_idx]['scapy_name']: 
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
        if not packet.haslayer(IP):
            return

        src_ip = packet[IP].src
        dst_port = None
        protocol = None

        if packet.haslayer(TCP):
            dst_port = packet[TCP].dport
            protocol = 'TCP'
        elif packet.haslayer(UDP):
            dst_port = packet[UDP].dport
            protocol = 'UDP'
        else:
            return

        if src_ip in self.threat_intel.malicious_ips:
            self.trigger_alert(
                f"Malicious {protocol} traffic from {src_ip} to port {dst_port} on {iface_name}", 
                'malicious'
            )

        if protocol == 'TCP' and packet[TCP].flags & 0x02:
            self.counters[src_ip]['syn'] += 1
            if self.counters[src_ip]['syn'] > self.config['thresholds']['syn']:
                self.trigger_alert(
                    f"SYN flood from {src_ip} to port {dst_port} on {iface_name}", 
                    'syn'
                )

        if dst_port not in self.known_ports[src_ip]:
            self.known_ports[src_ip].add(dst_port)
            self.counters[src_ip]['new_ports'] += 1
            if self.counters[src_ip]['new_ports'] > self.config['thresholds']['new_ports']:
                self.trigger_alert(
                    f"Port scan from {src_ip} to {protocol} port {dst_port} on {iface_name}", 
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

        print(f"\n[+] Starting monitoring...")
        self.running = True

        def sniff_target(iface_info):
            try:
                print(f"[+] Starting capture on {iface_info['name']}")
                sniff(
                    filter=('tcp or udp') + 
                    (f" and net {self.config['subnet_filter']}" if self.config['subnet_filter'] else ''),
                    prn=lambda p: self.packet_analyzer(p, iface_info['name']),
                    store=False,
                    stop_filter=lambda _: not self.running,
                    iface=iface_info['scapy_name']
                )
            except PermissionError:
                print(f"[!] Permission denied for interface {iface_info['name']}")
            except Exception as e:
                print(f"[!] Interface {iface_info['name']} error: {str(e)}")
            finally:
                if self.running:
                    self.running = False

        self.sniffers = []
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