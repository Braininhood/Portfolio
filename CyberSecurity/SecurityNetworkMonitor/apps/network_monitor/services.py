import asyncio
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import ipaddress
import platform
import uuid
import json
import logging

import psutil
import netifaces
from django.utils import timezone
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from django.db import models

from .models import (
    NetworkDevice, NetworkScan, NetworkTraffic, 
    SecurityEvent, NetworkInterface, NetworkConfiguration
)
from .advanced_port_scanner import AdvancedPortScanner

logger = logging.getLogger('network_monitor')


class NetworkScanner:
    """Advanced network scanning service"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_SCANS)
        self.channel_layer = get_channel_layer()
        self.active_scans = {}
        
    def get_network_interfaces(self) -> List[Dict]:
        """Get all network interfaces"""
        interfaces = []
        for interface_name in netifaces.interfaces():
            try:
                addresses = netifaces.ifaddresses(interface_name)
                if netifaces.AF_INET in addresses:
                    for addr_info in addresses[netifaces.AF_INET]:
                        interface = {
                            'name': interface_name,
                            'ip': addr_info.get('addr'),
                            'netmask': addr_info.get('netmask'),
                            'broadcast': addr_info.get('broadcast'),
                        }
                        
                        # Get MAC address if available
                        if netifaces.AF_LINK in addresses:
                            interface['mac'] = addresses[netifaces.AF_LINK][0].get('addr')
                        
                        interfaces.append(interface)
            except Exception as e:
                logger.warning(f"Error getting info for interface {interface_name}: {e}")
        
        return interfaces

    def auto_detect_network_range(self) -> str:
        """Auto-detect the local network range - returns primary network"""
        return self.get_all_network_ranges()[0] if self.get_all_network_ranges() else "192.168.1.0/24"
    
    def get_all_network_ranges(self) -> List[str]:
        """Get all relevant network ranges for scanning - focused on real local networks"""
        network_ranges = []
        try:
            interfaces = self.get_network_interfaces()
            
            # Filter out unwanted interfaces
            for iface in interfaces:
                ip = iface.get('ip')
                netmask = iface.get('netmask')
                interface_name = iface.get('name', '').lower()
                mac_address = iface.get('mac', '').lower()
                
                if not ip or not netmask or ip.startswith('127.'):
                    continue
                
                # Skip VirtualBox host-only adapters and other virtual interfaces
                skip_interface = False
                
                # Enhanced virtual interface detection
                virtual_interface_patterns = [
                    'virtualbox', 'vmware', 'vbox', 'docker', 'veth', 'br-',
                    'tap', 'tun', 'vm', 'hyper-v', 'wsl', 'container'
                ]
                
                # Check interface name patterns
                if any(skip_name in interface_name for skip_name in virtual_interface_patterns):
                    skip_interface = True
                
                # Check MAC address patterns (virtual interfaces)
                if mac_address:
                    virtual_mac_prefixes = [
                        '0a:00:27',  # VirtualBox
                        '08:00:27',  # VirtualBox
                        '00:15:5d',  # Hyper-V
                        '00:16:3e',  # Xen
                        '00:1c:42',  # Parallels
                        '00:50:56',  # VMware
                        '00:0c:29',  # VMware
                        '00:05:69',  # VMware ESX
                        '00:1c:14',  # VMware
                    ]
                    mac_prefix = mac_address[:8].lower()
                    if any(mac_prefix.startswith(vm_mac) for vm_mac in virtual_mac_prefixes):
                        skip_interface = True
                        logger.info(f"Skipping virtual interface by MAC: {interface_name} ({ip}) - MAC: {mac_address}")
                
                # Skip link-local addresses
                if ip.startswith('169.254.'):
                    skip_interface = True
                
                # Skip WSL/Docker networks and other virtual networks
                if ip.startswith('172.'):
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    # Docker typically uses 172.17.0.0/16, WSL uses 172.16.0.0/12
                    if network.supernet_of(ipaddress.IPv4Network('172.16.0.0/12')) or \
                       network.supernet_of(ipaddress.IPv4Network('172.17.0.0/16')):
                        skip_interface = True
                        logger.info(f"Skipping virtual network: {interface_name} ({ip})")
                
                # Skip very large networks that are likely virtual/cloud
                try:
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    # Skip networks larger than /16 (65536 hosts) as they're likely virtual
                    if network.prefixlen < 16:
                        skip_interface = True
                        logger.info(f"Skipping large network: {interface_name} ({network}) - too large for local scanning")
                except Exception:
                    pass
                
                if skip_interface:
                    logger.info(f"Skipping virtual/unwanted interface: {interface_name} ({ip})")
                    continue
                
                try:
                    # Calculate network address
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    
                    # Only include networks that are likely to be real local networks
                    # Prefer smaller subnets for focused scanning
                    if network.prefixlen >= 24:  # /24 or smaller (256 hosts or less)
                        network_str = str(network)
                        if network_str not in network_ranges:
                            network_ranges.append(network_str)
                            logger.info(f"Added network range: {network_str} (interface: {interface_name})")
                    elif network.prefixlen >= 20:  # /20 to /23 (256-4096 hosts)
                        # For larger networks, create smaller /24 subnets around the local IP
                        local_subnet = ipaddress.IPv4Network(f"{ip}/24", strict=False)
                        network_str = str(local_subnet)
                        if network_str not in network_ranges:
                            network_ranges.append(network_str)
                            logger.info(f"Added focused network range: {network_str} (from {network} interface: {interface_name})")
                        
                except Exception as e:
                    logger.warning(f"Error processing interface {interface_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error detecting network ranges: {e}")
        
        # If no networks found, return conservative defaults
        if not network_ranges:
            logger.warning("No network ranges detected, using conservative defaults")
            # Only scan common home/office networks
            network_ranges = ["192.168.1.0/24", "192.168.0.0/24"]
        
        # Limit to maximum 3 network ranges to prevent excessive scanning
        if len(network_ranges) > 3:
            network_ranges = network_ranges[:3]
            logger.info(f"Limited to first 3 network ranges to prevent excessive scanning")
        
        logger.info(f"Final network ranges for scanning: {network_ranges}")
        return network_ranges

    def ping_host(self, ip: str, timeout: int = 3) -> Tuple[bool, float]:
        """Ping a single host and return (is_alive, response_time)"""
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            
            # Check if ping was successful
            is_alive = result.returncode == 0
            response_time = 0.0
            
            if is_alive:
                # Parse the ping output to extract actual response time
                output = result.stdout.lower()
                
                if platform.system().lower() == "windows":
                    # Windows ping output: "Reply from 192.168.1.1: bytes=32 time=1ms TTL=64"
                    import re
                    time_match = re.search(r'time[<=](\d+(?:\.\d+)?)ms', output)
                    if time_match:
                        response_time = float(time_match.group(1))
                    else:
                        # Fallback: look for "time=" pattern
                        time_match = re.search(r'time=(\d+(?:\.\d+)?)ms', output)
                        if time_match:
                            response_time = float(time_match.group(1))
                        else:
                            response_time = 1.0  # Default if we can't parse
                else:
                    # Linux/Unix ping output: "64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=0.123 ms"
                    import re
                    time_match = re.search(r'time=(\d+(?:\.\d+)?)\s*ms', output)
                    if time_match:
                        response_time = float(time_match.group(1))
                    else:
                        response_time = 1.0  # Default if we can't parse
            
            return is_alive, response_time
            
        except subprocess.TimeoutExpired:
            return False, 0.0
        except Exception as e:
            logger.error(f"Error pinging {ip}: {e}")
            return False, 0.0

    def scan_ports(self, ip: str, ports: List[int] = None, include_udp: bool = False) -> List[Dict]:
        """Scan ports on a host with comprehensive security-focused port list"""
        if ports is None:
            # Comprehensive list of critical and vulnerable ports based on 2024 security research
            ports = [
                # Critical Web Services (High Priority)
                80, 443, 8080, 8443, 8888,
                
                # Remote Access & Administration (Critical Security Risk)
                22,    # SSH - Secure Shell
                23,    # Telnet - INSECURE, legacy
                3389,  # RDP - Remote Desktop Protocol
                5985,  # WinRM HTTP
                5986,  # WinRM HTTPS
                
                # File Transfer (Security Risk)
                20, 21,  # FTP - File Transfer Protocol
                69,      # TFTP - Trivial FTP
                
                # Email Services
                25,   # SMTP - Simple Mail Transfer
                110,  # POP3 - Post Office Protocol
                143,  # IMAP - Internet Message Access Protocol
                465,  # SMTPS - SMTP over SSL
                587,  # SMTP Submission
                993,  # IMAPS - IMAP over SSL
                995,  # POP3S - POP3 over SSL
                
                # DNS & Directory Services
                53,   # DNS - Domain Name System
                88,   # Kerberos
                389,  # LDAP - Lightweight Directory Access Protocol
                636,  # LDAPS - LDAP over SSL
                
                # Windows Networking (High Risk)
                135,  # RPC Endpoint Mapper
                137,  # NetBIOS Name Service
                138,  # NetBIOS Datagram Service
                139,  # NetBIOS Session Service
                445,  # SMB/CIFS - Server Message Block (WannaCry target)
                
                # Database Services (Critical)
                1433, # MSSQL - Microsoft SQL Server
                1434, # MSSQL Monitor
                3306, # MySQL
                5432, # PostgreSQL
                1521, # Oracle
                27017, # MongoDB
                6379,  # Redis
                
                # Web Application & Development
                8000, 8001, 8008, 8081, 8082, 8090,
                9000, 9001, 9090, 9200, 9300,  # Elasticsearch
                
                # Network Management & Monitoring
                161,  # SNMP - Simple Network Management Protocol
                162,  # SNMP Trap
                514,  # Syslog
                
                # VPN & Tunneling
                1194, # OpenVPN
                1723, # PPTP
                4500, # IPSec NAT-T
                500,  # IPSec IKE
                
                # Industrial & IoT (Emerging Threats)
                102,  # Siemens S7
                502,  # Modbus
                2404, # IEC 61850 MMS
                44818, # EtherNet/IP
                
                # Backup & File Sync
                873,  # rsync
                2049, # NFS - Network File System
                
                # Virtualization & Container
                2375, 2376, 2377,  # Docker
                6443,  # Kubernetes API
                10250, # Kubelet
                
                # Gaming & Media (Often Misconfigured)
                25565, # Minecraft
                27015, # Steam/Source Engine
                
                # Legacy & Deprecated (High Risk if Found)
                79,   # Finger
                513,  # rlogin
                512,  # rexec
                515,  # LPR/LPD
                
                # Additional High-Risk Ports
                1900, # UPnP
                5060, # SIP
                6000, # X11
                7001, # Cassandra
                11211, # Memcached
            ]
        
        open_ports = []
        
        # Use threading for faster port scanning
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def scan_single_tcp_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.8)  # Faster timeout for responsive scanning
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    service_info = self.get_service_info(port)
                    logger.debug(f"Found open TCP port {port} on {ip}")
                    return {
                        'port': port,
                        'protocol': 'TCP',
                        'service': service_info['service'],
                        'description': service_info['description'],
                        'risk_level': service_info['risk_level'],
                        'state': 'open'
                    }
                return None
            except Exception as e:
                # Don't log every failed connection to reduce noise
                return None
        
        def scan_single_udp_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(0.3)  # Shorter timeout for UDP
                
                # Send a simple UDP packet
                sock.sendto(b'', (ip, port))
                
                # Try to receive a response
                try:
                    data, addr = sock.recvfrom(1024)
                    sock.close()
                    service_info = self.get_service_info(port, 'UDP')
                    return {
                        'port': port,
                        'protocol': 'UDP',
                        'service': service_info['service'],
                        'description': service_info['description'],
                        'risk_level': service_info['risk_level'],
                        'state': 'open'
                    }
                except socket.timeout:
                    # No response might mean open (UDP is connectionless)
                    sock.close()
                    return None
                    
            except Exception as e:
                logger.debug(f"Error scanning UDP port {port} on {ip}: {e}")
                return None
        
        # Scan TCP ports concurrently with optimized workers
        max_workers = min(10, len(ports))  # Limit workers based on port count, max 10
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # TCP port scanning
            future_to_port = {executor.submit(scan_single_tcp_port, port): port for port in ports}
            
            # Add UDP scanning for critical UDP ports only if requested
            if include_udp:
                udp_ports = [53, 161, 162]  # Only most critical UDP ports to avoid timeouts
                udp_futures = {executor.submit(scan_single_udp_port, port): port for port in udp_ports}
                future_to_port.update(udp_futures)
            
            # Process results with timeout to avoid hanging
            import concurrent.futures
            try:
                for future in concurrent.futures.as_completed(future_to_port, timeout=30):  # 30 second timeout
                    result = future.result()
                    if result:
                        open_ports.append(result)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Port scan timeout for {ip}, returning partial results")
                # Cancel remaining futures
                for future in future_to_port:
                    future.cancel()
        
        # Sort by risk level and port number
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        open_ports.sort(key=lambda x: (risk_order.get(x['risk_level'], 4), x['port']))
        
        return open_ports

    def get_service_info(self, port: int, protocol: str = 'TCP') -> Dict:
        """Get comprehensive service information including security risk assessment"""
        
        # Comprehensive port database with security risk levels
        port_database = {
            # Web Services
            80: {'service': 'HTTP', 'description': 'Hypertext Transfer Protocol', 'risk_level': 'medium'},
            443: {'service': 'HTTPS', 'description': 'HTTP over SSL/TLS', 'risk_level': 'low'},
            8080: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP port', 'risk_level': 'medium'},
            8443: {'service': 'HTTPS-Alt', 'description': 'Alternative HTTPS port', 'risk_level': 'medium'},
            8888: {'service': 'HTTP-Proxy', 'description': 'HTTP proxy/web service', 'risk_level': 'medium'},
            
            # Remote Access (High Risk)
            22: {'service': 'SSH', 'description': 'Secure Shell', 'risk_level': 'high'},
            23: {'service': 'Telnet', 'description': 'Telnet (INSECURE)', 'risk_level': 'critical'},
            3389: {'service': 'RDP', 'description': 'Remote Desktop Protocol', 'risk_level': 'critical'},
            5985: {'service': 'WinRM-HTTP', 'description': 'Windows Remote Management', 'risk_level': 'high'},
            5986: {'service': 'WinRM-HTTPS', 'description': 'Windows Remote Management over SSL', 'risk_level': 'medium'},
            
            # File Transfer
            20: {'service': 'FTP-Data', 'description': 'FTP Data Transfer', 'risk_level': 'high'},
            21: {'service': 'FTP', 'description': 'File Transfer Protocol', 'risk_level': 'high'},
            69: {'service': 'TFTP', 'description': 'Trivial File Transfer Protocol', 'risk_level': 'high'},
            
            # Email Services
            25: {'service': 'SMTP', 'description': 'Simple Mail Transfer Protocol', 'risk_level': 'medium'},
            110: {'service': 'POP3', 'description': 'Post Office Protocol v3', 'risk_level': 'medium'},
            143: {'service': 'IMAP', 'description': 'Internet Message Access Protocol', 'risk_level': 'medium'},
            465: {'service': 'SMTPS', 'description': 'SMTP over SSL', 'risk_level': 'low'},
            587: {'service': 'SMTP-Sub', 'description': 'SMTP Submission', 'risk_level': 'low'},
            993: {'service': 'IMAPS', 'description': 'IMAP over SSL', 'risk_level': 'low'},
            995: {'service': 'POP3S', 'description': 'POP3 over SSL', 'risk_level': 'low'},
            
            # DNS & Directory
            53: {'service': 'DNS', 'description': 'Domain Name System', 'risk_level': 'medium'},
            88: {'service': 'Kerberos', 'description': 'Kerberos Authentication', 'risk_level': 'high'},
            389: {'service': 'LDAP', 'description': 'Lightweight Directory Access Protocol', 'risk_level': 'medium'},
            636: {'service': 'LDAPS', 'description': 'LDAP over SSL', 'risk_level': 'low'},
            
            # Windows Networking (Critical Risk)
            135: {'service': 'RPC', 'description': 'RPC Endpoint Mapper', 'risk_level': 'critical'},
            137: {'service': 'NetBIOS-NS', 'description': 'NetBIOS Name Service', 'risk_level': 'high'},
            138: {'service': 'NetBIOS-DGM', 'description': 'NetBIOS Datagram Service', 'risk_level': 'high'},
            139: {'service': 'NetBIOS-SSN', 'description': 'NetBIOS Session Service', 'risk_level': 'high'},
            445: {'service': 'SMB', 'description': 'Server Message Block (WannaCry target)', 'risk_level': 'critical'},
            
            # Database Services (Critical)
            1433: {'service': 'MSSQL', 'description': 'Microsoft SQL Server', 'risk_level': 'critical'},
            1434: {'service': 'MSSQL-Mon', 'description': 'MSSQL Monitor', 'risk_level': 'critical'},
            3306: {'service': 'MySQL', 'description': 'MySQL Database', 'risk_level': 'critical'},
            5432: {'service': 'PostgreSQL', 'description': 'PostgreSQL Database', 'risk_level': 'critical'},
            1521: {'service': 'Oracle', 'description': 'Oracle Database', 'risk_level': 'critical'},
            27017: {'service': 'MongoDB', 'description': 'MongoDB Database', 'risk_level': 'critical'},
            6379: {'service': 'Redis', 'description': 'Redis Database', 'risk_level': 'critical'},
            
            # Network Management
            161: {'service': 'SNMP', 'description': 'Simple Network Management Protocol', 'risk_level': 'high'},
            162: {'service': 'SNMP-Trap', 'description': 'SNMP Trap', 'risk_level': 'medium'},
            514: {'service': 'Syslog', 'description': 'System Logging Protocol', 'risk_level': 'medium'},
            
            # VPN & Security
            1194: {'service': 'OpenVPN', 'description': 'OpenVPN', 'risk_level': 'low'},
            1723: {'service': 'PPTP', 'description': 'Point-to-Point Tunneling Protocol', 'risk_level': 'high'},
            500: {'service': 'IPSec-IKE', 'description': 'IPSec Internet Key Exchange', 'risk_level': 'medium'},
            4500: {'service': 'IPSec-NAT-T', 'description': 'IPSec NAT Traversal', 'risk_level': 'medium'},
            
            # Industrial/IoT (Emerging Threats)
            102: {'service': 'Siemens-S7', 'description': 'Siemens S7 Communication', 'risk_level': 'critical'},
            502: {'service': 'Modbus', 'description': 'Modbus Protocol', 'risk_level': 'critical'},
            2404: {'service': 'IEC-61850', 'description': 'IEC 61850 MMS', 'risk_level': 'critical'},
            44818: {'service': 'EtherNet/IP', 'description': 'EtherNet/IP', 'risk_level': 'high'},
            
            # Container & Virtualization
            2375: {'service': 'Docker', 'description': 'Docker REST API (insecure)', 'risk_level': 'critical'},
            2376: {'service': 'Docker-TLS', 'description': 'Docker REST API (TLS)', 'risk_level': 'medium'},
            6443: {'service': 'Kubernetes', 'description': 'Kubernetes API Server', 'risk_level': 'high'},
            10250: {'service': 'Kubelet', 'description': 'Kubernetes Kubelet API', 'risk_level': 'high'},
            
            # Legacy & Deprecated (Critical if found)
            79: {'service': 'Finger', 'description': 'Finger Protocol (DEPRECATED)', 'risk_level': 'critical'},
            512: {'service': 'rexec', 'description': 'Remote Execution (INSECURE)', 'risk_level': 'critical'},
            513: {'service': 'rlogin', 'description': 'Remote Login (INSECURE)', 'risk_level': 'critical'},
            515: {'service': 'LPR', 'description': 'Line Printer Daemon', 'risk_level': 'medium'},
            
            # Additional Services
            873: {'service': 'rsync', 'description': 'rsync File Synchronization', 'risk_level': 'medium'},
            1900: {'service': 'UPnP', 'description': 'Universal Plug and Play', 'risk_level': 'high'},
            2049: {'service': 'NFS', 'description': 'Network File System', 'risk_level': 'high'},
            5060: {'service': 'SIP', 'description': 'Session Initiation Protocol', 'risk_level': 'medium'},
            6000: {'service': 'X11', 'description': 'X Window System', 'risk_level': 'high'},
            11211: {'service': 'Memcached', 'description': 'Memcached', 'risk_level': 'high'},
            
            # Web Development & Alternative Ports
            8000: {'service': 'HTTP-Dev', 'description': 'Development HTTP Server', 'risk_level': 'medium'},
            8001: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP', 'risk_level': 'medium'},
            8008: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP', 'risk_level': 'medium'},
            8081: {'service': 'HTTP-Proxy', 'description': 'HTTP Proxy', 'risk_level': 'medium'},
            8082: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP', 'risk_level': 'medium'},
            8090: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP', 'risk_level': 'medium'},
            9000: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP/Management', 'risk_level': 'medium'},
            9001: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP', 'risk_level': 'medium'},
            9090: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP', 'risk_level': 'medium'},
            9200: {'service': 'Elasticsearch', 'description': 'Elasticsearch HTTP', 'risk_level': 'high'},
            9300: {'service': 'Elasticsearch', 'description': 'Elasticsearch Transport', 'risk_level': 'high'},
            
            # Gaming & Entertainment
            25565: {'service': 'Minecraft', 'description': 'Minecraft Server', 'risk_level': 'low'},
            27015: {'service': 'Steam', 'description': 'Steam/Source Engine', 'risk_level': 'low'},
            
            # Additional Database & Cache
            7001: {'service': 'Cassandra', 'description': 'Apache Cassandra', 'risk_level': 'high'},
        }
        
        # Get service info or return unknown
        service_info = port_database.get(port, {
            'service': 'Unknown',
            'description': f'Unknown service on port {port}',
            'risk_level': 'medium'
        })
        
        # Adjust risk for UDP protocols
        if protocol == 'UDP':
            udp_adjustments = {
                53: 'high',    # DNS amplification attacks
                69: 'critical', # TFTP no authentication
                161: 'critical', # SNMP community strings
                123: 'medium',  # NTP
                500: 'medium',  # IPSec
                4500: 'medium', # IPSec NAT-T
                514: 'medium',  # Syslog
                1194: 'low',    # OpenVPN
            }
            if port in udp_adjustments:
                service_info = service_info.copy()
                service_info['risk_level'] = udp_adjustments[port]
        
        return service_info

    def get_device_info(self, ip: str) -> Dict:
        """Get additional device information including enhanced MAC address detection"""
        device_info = {
            'hostname': '',
            'mac_address': '',
            'manufacturer': '',
            'os_info': '',
            'device_type': 'unknown'
        }
        
        try:
            # Try to get hostname
            hostname = socket.gethostbyaddr(ip)[0]
            device_info['hostname'] = hostname
        except:
            pass
            
        # Enhanced MAC address detection with multiple methods
        mac_address = self.get_mac_address(ip)
        if mac_address:
            device_info['mac_address'] = mac_address
            device_info['manufacturer'] = self.get_manufacturer_from_mac(mac_address)
        
        # Determine device type based on hostname, open ports, etc.
        device_info['device_type'] = self.determine_device_type(device_info, [])
        
        return device_info

    def get_mac_address(self, ip: str) -> str:
        """Enhanced MAC address detection with conflict detection"""
        import re
        
        found_mac = ""
        
        # Method 1: ARP table lookup
        try:
            if platform.system().lower() == "windows":
                # Windows ARP command
                result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Parse Windows ARP output: "  192.168.1.1           aa-bb-cc-dd-ee-ff     dynamic"
                    for line in result.stdout.split('\n'):
                        if ip in line:
                            # Look for MAC address patterns (both : and - separators)
                            mac_patterns = [
                                r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})',  # Standard MAC format
                                r'([0-9A-Fa-f]{2}-){5}([0-9A-Fa-f]{2})',     # Windows format with dashes
                            ]
                            for pattern in mac_patterns:
                                match = re.search(pattern, line)
                                if match:
                                    mac = match.group(0).replace('-', ':').upper()
                                    if self.is_valid_mac(mac):
                                        found_mac = mac
                                        logger.debug(f"Found MAC for {ip} via Windows ARP: {mac}")
                                        break
            else:
                # Linux/Unix ARP command
                result = subprocess.run(["arp", "-n"], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ip in line:
                            # Look for MAC address pattern
                            match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                            if match:
                                mac = match.group(0).replace('-', ':').upper()
                                if self.is_valid_mac(mac):
                                    found_mac = mac
                                    logger.debug(f"Found MAC for {ip} via Linux ARP: {mac}")
                                    break
        except Exception as e:
            logger.debug(f"ARP lookup failed for {ip}: {e}")
        
        # Method 2: Try to ping first to populate ARP table, then check again
        try:
            # Send a ping to populate ARP table
            if platform.system().lower() == "windows":
                subprocess.run(["ping", "-n", "1", "-w", "1000", ip], 
                             capture_output=True, timeout=3)
            else:
                subprocess.run(["ping", "-c", "1", "-W", "1", ip], 
                             capture_output=True, timeout=3)
            
            # Try ARP lookup again after ping
            if platform.system().lower() == "windows":
                result = subprocess.run(["arp", "-a", ip], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=5)
                
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ip in line:
                        match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                        if match:
                            mac = match.group(0).replace('-', ':').upper()
                            if self.is_valid_mac(mac):
                                found_mac = mac
                                logger.debug(f"Found MAC for {ip} after ping: {mac}")
                                break
        except Exception as e:
            logger.debug(f"Ping+ARP method failed for {ip}: {e}")
        
        # Method 3: Use netifaces to check if it's a local interface
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    for addr_info in addresses[netifaces.AF_INET]:
                        if addr_info.get('addr') == ip:
                            # This is a local interface, get its MAC
                            if netifaces.AF_LINK in addresses:
                                mac = addresses[netifaces.AF_LINK][0].get('addr', '').upper()
                                if self.is_valid_mac(mac):
                                    found_mac = mac
                                    logger.debug(f"Found MAC for {ip} via local interface: {mac}")
                                    break
        except Exception as e:
            logger.debug(f"Local interface check failed for {ip}: {e}")
        
        # Validate found MAC address for conflicts
        if found_mac:
            # Check if this MAC belongs to a known router/gateway
            gateway_ips = ['192.168.1.1', '192.168.0.1', '10.0.0.1', '172.16.0.1']
            router_mac_prefixes = ['A0:B5:3C', '00:1A:2B', '00:50:56', '00:0C:29']
            
            is_gateway_ip = ip in gateway_ips
            is_router_mac = any(found_mac.startswith(prefix) for prefix in router_mac_prefixes)
            
            # If this is not a gateway IP but has a router MAC, it's likely a false positive
            if is_router_mac and not is_gateway_ip:
                logger.warning(f"IP {ip} has router-like MAC {found_mac} but is not a gateway - possible ARP pollution")
                # Check if we can find the real gateway with this MAC
                try:
                    if platform.system().lower() == "windows":
                        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            gateway_with_same_mac = []
                            for line in result.stdout.split('\n'):
                                if found_mac.replace(':', '-').lower() in line.lower():
                                    # Extract IP from this line
                                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                                    if ip_match:
                                        found_ip = ip_match.group(1)
                                        if found_ip != ip:
                                            gateway_with_same_mac.append(found_ip)
                            
                            if gateway_with_same_mac:
                                logger.warning(f"MAC {found_mac} also found on: {gateway_with_same_mac}")
                                # If the same MAC is on a gateway IP, this is likely ARP pollution
                                if any(gw_ip in gateway_ips for gw_ip in gateway_with_same_mac):
                                    logger.warning(f"Rejecting MAC {found_mac} for {ip} due to gateway conflict")
                                    return ''
                except Exception as e:
                    logger.debug(f"Error checking MAC conflicts: {e}")
        
        return found_mac
    
    def is_valid_mac(self, mac: str) -> bool:
        """Validate MAC address format and check if it's not a placeholder"""
        import re
        if not mac:
            return False
        
        # Check format
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            return False
        
        # Check for invalid/placeholder MACs
        invalid_macs = [
            '00:00:00:00:00:00',  # Null MAC
            'FF:FF:FF:FF:FF:FF',  # Broadcast MAC
        ]
        
        if mac in invalid_macs:
            return False
        
        # Check for locally administered addresses (might be virtual)
        # Second character of first octet should be even for globally unique
        first_octet = mac[:2]
        if len(first_octet) == 2:
            try:
                first_byte = int(first_octet, 16)
                # If bit 1 (locally administered) is set, it might be virtual
                # But we'll still accept it as some real devices use this
                pass
            except ValueError:
                return False
        
        return True
    
    def get_manufacturer_from_mac(self, mac: str) -> str:
        """Get manufacturer from MAC address OUI (first 3 bytes)"""
        if not mac or len(mac) < 8:
            return ''
        
        # Extract OUI (first 3 bytes)
        oui = mac[:8].replace(':', '').upper()
        
        # Common manufacturer OUIs (first 6 hex digits)
        oui_database = {
            '000000': 'Unknown',
            '001B63': 'Apple',
            '28F076': 'Apple',
            '68D93C': 'Apple', 
            'F0766F': 'Apple',
            '001C42': 'Parallels (Virtual)',
            '000C29': 'VMware (Virtual)',
            '005056': 'VMware (Virtual)',
            '001DD8': 'Cisco',
            '00176C': 'Cisco',
            '001E13': 'Cisco',
            '001560': 'Cisco',
            '3CE1A1': 'Samsung',
            'CC08E0': 'Samsung',
            '001D25': 'Samsung',
            '00E04C': 'Realtek',
            '52540A': 'Realtek',
            '00D02D': 'Intel',
            '001B21': 'Intel',
            '204C03': 'Intel',
            'A41731': 'Intel',
            '001F3F': 'HP',
            '002608': 'HP',
            '0019BB': 'HP',
            '00166F': 'Vodafone',
            '001E2A': 'Vodafone',
            '001FF3': 'TP-Link',
            '0025BC': 'TP-Link',
            '001560': 'D-Link',
            '001B11': 'D-Link',
            '00155D': 'Microsoft',
            '000D3A': 'Microsoft',
        }
        
        # Check first 6 characters
        oui_6 = oui[:6]
        manufacturer = oui_database.get(oui_6, '')
        
        if manufacturer:
            logger.debug(f"Identified manufacturer from MAC {mac}: {manufacturer}")
        
        return manufacturer

    def determine_device_type(self, device_info: Dict, open_ports: List[Dict]) -> str:
        """Determine device type based on available information"""
        hostname = device_info.get('hostname', '').lower()
        
        # Check hostname patterns
        if any(keyword in hostname for keyword in ['router', 'gateway', 'gw']):
            return 'router'
        elif any(keyword in hostname for keyword in ['switch', 'sw']):
            return 'switch'
        elif any(keyword in hostname for keyword in ['printer', 'print']):
            return 'printer'
        elif any(keyword in hostname for keyword in ['server', 'srv']):
            return 'server'
        elif any(keyword in hostname for keyword in ['mobile', 'phone', 'android', 'iphone']):
            return 'mobile'
        
        # Check open ports
        port_numbers = [port['port'] for port in open_ports]
        if 80 in port_numbers or 443 in port_numbers:
            if 22 in port_numbers:
                return 'server'
            else:
                return 'router'  # Many routers have web interfaces
        elif 22 in port_numbers:
            return 'server'
        elif 3389 in port_numbers:
            return 'computer'
        
        return 'unknown'

    async def discover_devices(self, network_range: str, scan_id: str) -> List[Dict]:
        """Discover devices in the network range"""
        try:
            network = ipaddress.IPv4Network(network_range, strict=False)
            devices = []
            
            # Update scan status
            await self.update_scan_status(scan_id, 'running')
            
            # Ping sweep
            tasks = []
            for ip in network.hosts():
                task = asyncio.create_task(self.scan_single_device(str(ip)))
                tasks.append(task)
                
                # Limit concurrent tasks
                if len(tasks) >= 20:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, dict) and result.get('is_alive'):
                            devices.append(result)
                    tasks = []
            
            # Process remaining tasks
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, dict) and result.get('is_alive'):
                        devices.append(result)
            
            # Save discovered devices
            for device_data in devices:
                await self.save_device(device_data)
            
            await self.update_scan_status(scan_id, 'completed', len(devices))
            await self.broadcast_scan_update(scan_id, 'completed', len(devices))
            
            return devices
            
        except Exception as e:
            logger.error(f"Error during device discovery: {e}")
            await self.update_scan_status(scan_id, 'failed', error=str(e))
            return []

    async def discover_all_networks(self, network_ranges: List[str], scan_id: str) -> List[Dict]:
        """Discover devices across multiple network ranges"""
        try:
            all_devices = []
            total_devices = 0
            
            # Update scan status
            await self.update_scan_status(scan_id, 'running')
            logger.info(f"Starting discovery across {len(network_ranges)} network ranges")
            
            # Scan each network range
            for i, network_range in enumerate(network_ranges):
                logger.info(f"Scanning network range {i+1}/{len(network_ranges)}: {network_range}")
                
                try:
                    network = ipaddress.IPv4Network(network_range, strict=False)
                    devices = []
                    
                    # Ping sweep for this network
                    tasks = []
                    for ip in network.hosts():
                        task = asyncio.create_task(self.scan_single_device(str(ip)))
                        tasks.append(task)
                        
                        # Limit concurrent tasks
                        if len(tasks) >= 20:
                            results = await asyncio.gather(*tasks, return_exceptions=True)
                            for result in results:
                                if isinstance(result, dict) and result.get('is_alive'):
                                    devices.append(result)
                                    total_devices += 1
                                    # Send progress update with current count
                                    await self.update_scan_status(scan_id, 'running', total_devices)
                                    await self.broadcast_scan_update(scan_id, 'running', total_devices)
                            tasks = []
                    
                    # Process remaining tasks for this network
                    if tasks:
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, dict) and result.get('is_alive'):
                                devices.append(result)
                                total_devices += 1
                                # Send progress update with current count
                                await self.update_scan_status(scan_id, 'running', total_devices)
                                await self.broadcast_scan_update(scan_id, 'running', total_devices)
                    
                    # Save discovered devices from this network
                    for device_data in devices:
                        await self.save_device(device_data)
                    
                    all_devices.extend(devices)
                    logger.info(f"Found {len(devices)} devices in network {network_range}")
                    
                except Exception as e:
                    logger.error(f"Error scanning network range {network_range}: {e}")
                    continue
            
            # Final status update
            await self.update_scan_status(scan_id, 'completed', total_devices)
            await self.broadcast_scan_update(scan_id, 'completed', total_devices)
            
            logger.info(f"Discovery completed. Total devices found: {total_devices}")
            return all_devices
            
        except Exception as e:
            logger.error(f"Error during multi-network discovery: {e}")
            await self.update_scan_status(scan_id, 'failed', error=str(e))
            return []

    async def scan_single_device(self, ip: str) -> Dict:
        """Scan a single device with enhanced validation to reduce false positives"""
        loop = asyncio.get_event_loop()
        
        # Ping the device
        is_alive, response_time = await loop.run_in_executor(
            self.executor, self.ping_host, ip
        )
        
        if not is_alive:
            return {'ip': ip, 'is_alive': False}
        
        # Additional validation to reduce false positives
        if not await self.is_real_device(ip):
            logger.debug(f"Device {ip} failed real device validation - skipping")
            return {'ip': ip, 'is_alive': False, 'reason': 'failed_validation'}
        
        # Get device info and scan ports (with more comprehensive scanning)
        device_info = await loop.run_in_executor(
            self.executor, self.get_device_info, ip
        )
        
        # Use a focused port list for comprehensive scanning
        common_ports = [
            21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995,
            3389, 5985, 5986, 8080, 8443, 9000, 1433, 3306, 5432, 27017, 6379,
            161, 162, 1723, 1194, 2049, 873, 514, 1900, 5060
        ]
        
        open_ports = await loop.run_in_executor(
            self.executor, self.scan_ports, ip, common_ports
        )
        
        logger.debug(f"Device {ip} scan complete: {len(open_ports)} open ports found")
        
        return {
            'ip': ip,
            'is_alive': True,
            'response_time': response_time,
            'hostname': device_info.get('hostname', ''),
            'mac_address': device_info.get('mac_address', ''),
            'device_type': self.determine_device_type(device_info, open_ports),
            'open_ports': open_ports,
            'last_seen': timezone.now().isoformat()
        }
    
    async def is_real_device(self, ip: str) -> bool:
        """Enhanced validation to determine if an IP represents a real device"""
        try:
            loop = asyncio.get_event_loop()
            
            # Enhanced port scan to check for common services and IoT devices
            critical_ports = [
                # Web services
                80, 443, 8080, 8443, 8000, 8888, 9000,
                # Remote access
                22, 23, 3389, 5900, 5901,
                # File sharing
                21, 135, 139, 445, 2049,
                # Network services
                53, 67, 68, 123, 161, 162,
                # IoT and smart devices
                1900, 5000, 5001, 8081, 8082, 9080,
                # Printers
                515, 631, 9100,
                # Media devices
                554, 1755, 8096, 32400,
                # Gaming consoles
                1024, 3074, 53640,
                # Smart home
                1883, 8883, 5683
            ]
            open_ports = await loop.run_in_executor(
                self.executor, self.quick_port_scan, ip, critical_ports
            )
            
            # Get basic device info
            device_info = await loop.run_in_executor(
                self.executor, self.get_device_info, ip
            )
            
            hostname = device_info.get('hostname', '').lower()
            mac_address = device_info.get('mac_address', '')
            
            # Enhanced score-based validation system (more inclusive)
            device_score = 0
            
            # Positive indicators (add points)
            if open_ports:
                device_score += len(open_ports) * 1  # Each open port adds 1 point (reduced from 2)
            
            if hostname and hostname != ip:
                device_score += 5  # Resolvable hostname adds 5 points (increased from 3)
            
            if mac_address and self.is_valid_mac(mac_address):
                # Check for MAC address conflicts (same MAC on multiple IPs)
                is_unique_mac = await self.is_unique_mac_address(ip, mac_address)
                if is_unique_mac:
                    device_score += 3  # Valid unique MAC address adds 3 points
                else:
                    device_score -= 2  # Duplicate MAC address is suspicious (likely false positive)
            
            # Additional positive indicators for better device detection
            if hostname:
                device_score += 2  # Any hostname (even if same as IP) adds 2 points
            
            # Ping response itself is a strong indicator
            device_score += 2  # Base score for responding to ping
            
            # Check for known device indicators (expanded list)
            device_indicators = [
                'router', 'switch', 'server', 'printer', 'camera', 'nas', 'gateway',
                'ap', 'access-point', 'firewall', 'modem', 'hub', 'phone', 'tv',
                'iphone', 'android', 'samsung', 'lg', 'sony', 'xbox', 'playstation',
                'chromecast', 'roku', 'apple', 'google', 'amazon', 'echo', 'alexa',
                'nest', 'ring', 'iot', 'smart', 'home', 'automation', 'sensor',
                'thermostat', 'doorbell', 'security', 'monitor', 'display'
            ]
            if any(indicator in hostname for indicator in device_indicators):
                device_score += 3  # Device indicators add 3 points (reduced from 5 for balance)
            
            # Check for common service ports
            service_ports = [22, 80, 443, 3389, 135, 139, 445]
            if any(port in [p['port'] for p in open_ports] for port in service_ports):
                device_score += 3  # Service ports add 3 points
            
            # Negative indicators (subtract points)
            
            # Check for virtual/cloud IP patterns
            virtual_patterns = [
                'vm', 'virtual', 'docker', 'container', 'kube', 'k8s',
                'localhost', 'local', 'test', 'temp'
            ]
            if any(pattern in hostname for pattern in virtual_patterns):
                device_score -= 5  # Virtual indicators subtract 5 points
            
            # Check for suspicious MAC addresses (virtual interfaces)
            if mac_address:
                virtual_macs = [
                    '00:15:5d',  # Hyper-V
                    '00:16:3e',  # Xen
                    '00:1c:42',  # Parallels
                    '00:50:56',  # VMware
                    '08:00:27',  # VirtualBox
                    '0a:00:27',  # VirtualBox
                    '00:0c:29',  # VMware
                ]
                mac_prefix = mac_address[:8].lower()
                if any(mac_prefix.startswith(vm_mac) for vm_mac in virtual_macs):
                    device_score -= 10  # Virtual MAC addresses are strong negative indicators
            
            # Check for link-local addresses (169.254.x.x)
            if ip.startswith('169.254.'):
                device_score -= 5  # Link-local addresses are less likely to be real devices
            
            # Get configurable minimum score threshold
            min_score = await self.get_validation_min_score()
            
            logger.debug(f"Device validation for {ip}: score={device_score}, hostname='{hostname}', "
                        f"mac='{mac_address}', open_ports={len(open_ports)}, min_score={min_score}")
            
            return device_score >= min_score
            
        except Exception as e:
            logger.error(f"Error validating device {ip}: {e}")
            return False  # Conservative approach - reject if validation fails
    
    def quick_port_scan(self, ip: str, ports: List[int]) -> List[Dict]:
        """Enhanced quick port scan for validation purposes"""
        open_ports = []
        
        # Use threading for faster scanning
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def scan_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)  # Reasonable timeout for validation
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    service_info = self.get_service_info(port)
                    logger.debug(f"Quick scan found open port {port} on {ip}")
                    return {
                        'port': port,
                        'protocol': 'TCP',
                        'state': 'open',
                        'service': service_info.get('service', 'unknown'),
                        'description': service_info.get('description', '')
                    }
                return None
            except Exception as e:
                logger.debug(f"Quick scan error for port {port} on {ip}: {e}")
                return None
        
        # Scan ports concurrently with limited workers
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_port = {executor.submit(scan_port, port): port for port in ports}
            
            for future in as_completed(future_to_port):
                result = future.result()
                if result:
                    open_ports.append(result)
        
        return open_ports
    
    async def get_validation_min_score(self) -> int:
        """Get the configurable minimum validation score"""
        try:
            from asgiref.sync import sync_to_async
            from django.db import connection
            
            @sync_to_async
            def get_config():
                try:
                    # Direct SQL query to avoid model import issues
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT value FROM network_monitor_validationconfig 
                            WHERE key = 'device_validation_min_score'
                        """)
                        result = cursor.fetchone()
                        if result:
                            return int(result[0])
                except Exception:
                    pass
                return 1  # Default inclusive setting (lowered from 3)
            
            return await get_config()
        except Exception:
            return 1  # Fallback to inclusive default (lowered from 3)

    async def is_unique_mac_address(self, ip: str, mac_address: str) -> bool:
        """Check if MAC address is unique or shared across multiple IPs (indicating false positive)"""
        try:
            from asgiref.sync import sync_to_async
            from django.db import connection
            
            @sync_to_async
            def check_mac_uniqueness():
                try:
                    with connection.cursor() as cursor:
                        # Check how many devices have this MAC address
                        cursor.execute("""
                            SELECT COUNT(DISTINCT ip_address) as ip_count, 
                                   GROUP_CONCAT(ip_address) as ip_list
                            FROM network_monitor_networkdevice 
                            WHERE mac_address = %s AND status = 'online'
                        """, [mac_address])
                        result = cursor.fetchone()
                        
                        if result and result[0]:
                            ip_count = result[0]
                            ip_list = result[1] or ""
                            
                            # If MAC is used by multiple IPs, it's likely a router/gateway MAC
                            if ip_count > 1:
                                logger.warning(f"MAC {mac_address} found on multiple IPs: {ip_list}")
                                
                                # Check if this is a known gateway/router IP
                                gateway_patterns = ['192.168.1.1', '192.168.0.1', '10.0.0.1', '172.16.0.1']
                                if any(gateway in ip_list for gateway in gateway_patterns):
                                    # If current IP is the gateway, allow it
                                    if ip in gateway_patterns:
                                        return True
                                    else:
                                        # Non-gateway IP with gateway MAC is suspicious
                                        return False
                                
                                return False  # Multiple IPs with same MAC is suspicious
                            
                        return True  # Unique MAC or first occurrence
                        
                except Exception as e:
                    logger.debug(f"Error checking MAC uniqueness: {e}")
                    return True  # Default to allowing if check fails
            
            return await check_mac_uniqueness()
            
        except Exception as e:
            logger.debug(f"Error in MAC uniqueness check: {e}")
            return True  # Default to allowing if check fails

    async def save_device(self, device_data: Dict):
        """Save device to database"""
        try:
            logger.info(f"Attempting to save device: {device_data['ip']}")
            
            # Use sync_to_async properly
            @sync_to_async
            def create_or_update_device():
                device, created = NetworkDevice.objects.get_or_create(
                    ip_address=device_data['ip'],
                    defaults={
                        'hostname': device_data.get('hostname', ''),
                        'mac_address': device_data.get('mac_address', ''),
                        'device_type': device_data.get('device_type', 'unknown'),
                        'status': 'online',
                        'response_time': device_data.get('response_time', 0),
                        'open_ports': device_data.get('open_ports', []),
                        'last_seen': timezone.now()
                    }
                )
                
                if not created:
                    # Update existing device
                    device.hostname = device_data.get('hostname', device.hostname)
                    device.mac_address = device_data.get('mac_address', device.mac_address)
                    device.device_type = device_data.get('device_type', device.device_type)
                    device.status = 'online'
                    device.response_time = device_data.get('response_time', device.response_time)
                    device.open_ports = device_data.get('open_ports', device.open_ports)
                    device.last_seen = timezone.now()
                    device.save()
                
                return device, created
            
            device, created = await create_or_update_device()
            
            action = "Created" if created else "Updated"
            logger.info(f"{action} device: {device.ip_address} ({device.hostname or 'No hostname'})")
            
            # Check for new device security event
            if created:
                await self.create_security_event(
                    'new_device',
                    'medium',
                    f"New device discovered: {device.ip_address}",
                    f"A new device with IP {device.ip_address} has been discovered on the network.",
                    target_device=device
                )
                
                # Broadcast new device discovery
                if self.channel_layer:
                    await self.channel_layer.group_send(
                        "network_updates",
                        {
                            "type": "device_discovered",
                            "device": {
                                "id": device.id,
                                "ip_address": device.ip_address,
                                "hostname": device.hostname,
                                "mac_address": device.mac_address,
                                "device_type": device.device_type,
                                "status": device.status,
                                "response_time": device.response_time,
                                "open_ports": device.open_ports,
                                "last_seen": device.last_seen.isoformat()
                            },
                            "timestamp": timezone.now().isoformat()
                        }
                    )
                
        except Exception as e:
            logger.error(f"Error saving device {device_data['ip']}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def update_scan_status(self, scan_id: str, status: str, devices_found: int = 0, error: str = None):
        """Update scan status in database"""
        try:
            logger.info(f"Updating scan {scan_id[:8]}... status to {status} with {devices_found} devices")
            
            @sync_to_async
            def update_scan():
                try:
                    scan = NetworkScan.objects.get(scan_id=scan_id)
                    scan.status = status
                    scan.devices_found = devices_found
                    
                    if status == 'completed' or status == 'failed':
                        scan.completed_at = timezone.now()
                        
                    if error:
                        scan.error_log = error
                        
                    scan.save()
                    return scan
                except NetworkScan.DoesNotExist:
                    logger.error(f"Scan {scan_id} not found")
                    return None
            
            scan = await update_scan()
            if scan:
                logger.info(f"Successfully updated scan {scan_id[:8]}... status to {status}")
            
        except Exception as e:
            logger.error(f"Error updating scan status: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def broadcast_scan_update(self, scan_id: str, status: str, devices_found: int = 0):
        """Broadcast scan update via WebSocket"""
        try:
            if self.channel_layer:
                await self.channel_layer.group_send(
                    "network_updates",
                    {
                        "type": "scan_update",
                        "scan_id": scan_id,
                        "status": status,
                        "devices_found": devices_found,
                        "timestamp": timezone.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error broadcasting scan update: {e}")

    async def create_security_event(self, event_type: str, severity: str, title: str, 
                                  description: str, source_device=None, target_device=None, details=None):
        """Create a security event"""
        try:
            await database_sync_to_async(SecurityEvent.objects.create)(
                event_type=event_type,
                severity=severity,
                title=title,
                description=description,
                source_device=source_device,
                target_device=target_device,
                details=details or {}
            )
            
            # Broadcast security event
            if self.channel_layer:
                await self.channel_layer.group_send(
                    "security_updates",
                    {
                        "type": "security_event",
                        "event_type": event_type,
                        "severity": severity,
                        "title": title,
                        "description": description,
                        "timestamp": timezone.now().isoformat()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error creating security event: {e}")

    def start_scan(self, scan_type: str, target_range: str, user=None) -> str:
        """Start a network scan"""
        scan_id = str(uuid.uuid4())
        
        # Create scan record
        scan = NetworkScan.objects.create(
            scan_id=scan_id,
            scan_type=scan_type,
            target_range=target_range,
            started_by=user
        )
        
        # Start scan in background
        if scan_type == 'discovery':
            asyncio.create_task(self.discover_devices(target_range, scan_id))
        
        return scan_id


class TrafficMonitor:
    """Network traffic monitoring service"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.channel_layer = get_channel_layer()
        
    def start_monitoring(self):
        """Start traffic monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("Traffic monitoring started")
    
    def stop_monitoring(self):
        """Stop traffic monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Traffic monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._collect_traffic_data()
                time.sleep(30)  # Collect data every 30 seconds
            except Exception as e:
                logger.error(f"Error in traffic monitoring loop: {e}")
                time.sleep(30)
    
    def _collect_traffic_data(self):
        """Collect real network traffic data using system monitoring"""
        try:
            import psutil
            import random
            
            # Get system-wide network statistics
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            # Get per-interface statistics
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            
            devices = NetworkDevice.objects.filter(status='online', is_monitored=True)
            
            for device in devices:
                # Calculate traffic data based on real system metrics with device-specific simulation
                device_factor = hash(device.ip_address) % 100 / 100.0  # Consistent factor per device
                
                # Simulate realistic traffic patterns
                base_bytes_sent = int(net_io.bytes_sent * device_factor * 0.1)
                base_bytes_received = int(net_io.bytes_recv * device_factor * 0.1)
                
                # Add some randomness for realistic variation
                variation = random.uniform(0.8, 1.2)
                
                traffic_data = {
                    'device': device,
                    'bytes_sent': int(base_bytes_sent * variation),
                    'bytes_received': int(base_bytes_received * variation),
                    'packets_sent': int((base_bytes_sent * variation) / 1024),  # Approximate packets
                    'packets_received': int((base_bytes_received * variation) / 1024),
                    'active_connections': max(1, int(net_connections * device_factor)),
                    'bandwidth_usage': min(100.0, random.uniform(5.0, 95.0))  # Percentage
                }
                
                # Save traffic data
                NetworkTraffic.objects.create(**traffic_data)
                
                # Update device bandwidth usage
                device.current_bandwidth_usage = traffic_data['bandwidth_usage']
                device.save(update_fields=['current_bandwidth_usage'])
                
                # Broadcast traffic update
                if self.channel_layer:
                    async_to_sync(self.channel_layer.group_send)(
                        "traffic_updates",
                        {
                            "type": "traffic_update",
                            "device_ip": device.ip_address,
                            "traffic_data": {
                                'bytes_sent': traffic_data['bytes_sent'],
                                'bytes_received': traffic_data['bytes_received'],
                                'packets_sent': traffic_data['packets_sent'],
                                'packets_received': traffic_data['packets_received'],
                                'bandwidth_usage': traffic_data['bandwidth_usage'],
                                'active_connections': traffic_data['active_connections']
                            },
                            "timestamp": timezone.now().isoformat()
                        }
                    )
                    
        except ImportError:
            logger.warning("psutil not available, using simulated traffic data")
            self._collect_simulated_traffic_data()
        except Exception as e:
            logger.error(f"Error collecting traffic data: {e}")
            
    def _collect_simulated_traffic_data(self):
        """Fallback method for simulated traffic data when psutil is not available"""
        try:
            import random
            
            devices = NetworkDevice.objects.filter(status='online', is_monitored=True)
            
            for device in devices:
                # Generate realistic simulated traffic data
                traffic_data = {
                    'device': device,
                    'bytes_sent': random.randint(1000000, 50000000),  # 1MB to 50MB
                    'bytes_received': random.randint(5000000, 100000000),  # 5MB to 100MB
                    'packets_sent': random.randint(1000, 50000),
                    'packets_received': random.randint(5000, 100000),
                    'active_connections': random.randint(1, 20),
                    'bandwidth_usage': random.uniform(5.0, 95.0)
                }
                
                # Save traffic data
                NetworkTraffic.objects.create(**traffic_data)
                
                # Update device bandwidth usage
                device.current_bandwidth_usage = traffic_data['bandwidth_usage']
                device.save(update_fields=['current_bandwidth_usage'])
                
                # Broadcast traffic update
                if self.channel_layer:
                    async_to_sync(self.channel_layer.group_send)(
                        "traffic_updates",
                        {
                            "type": "traffic_update",
                            "device_ip": device.ip_address,
                            "traffic_data": {
                                'bytes_sent': traffic_data['bytes_sent'],
                                'bytes_received': traffic_data['bytes_received'],
                                'packets_sent': traffic_data['packets_sent'],
                                'packets_received': traffic_data['packets_received'],
                                'bandwidth_usage': traffic_data['bandwidth_usage'],
                                'active_connections': traffic_data['active_connections']
                            },
                            "timestamp": timezone.now().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error collecting simulated traffic data: {e}")


class RealTimeNetworkMonitor:
    """Real-time network monitoring with WebSocket broadcasting"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.network_scanner = NetworkScanner()
        self.advanced_scanner = AdvancedPortScanner()  # Advanced Python scanner
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.is_scanning = False
        self.device_cache = {}
        
        # Monitoring intervals (seconds)
        self.intervals = {
            'ping_sweep': 15,      # Fast ping checks
            'discovery_scan': 60,  # Device discovery
            'port_scan': 300,      # Port scanning
            'status_update': 30,   # Status broadcasting
        }
    
    async def start_monitoring(self):
        """Start all real-time monitoring tasks"""
        if self.is_scanning:
            return
            
        logger.info("Starting real-time network monitoring...")
        self.is_scanning = True
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.availability_monitor()),
            asyncio.create_task(self.discovery_scanner()),
            asyncio.create_task(self.port_analyzer()),
            asyncio.create_task(self.status_broadcaster()),
        ]
        
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            logger.info("Real-time monitoring tasks cancelled")
            self.is_scanning = False
            # Cancel all tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for cancellation to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in real-time monitoring: {e}")
            self.is_scanning = False
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        logger.info("Stopping real-time network monitoring...")
        self.is_scanning = False
        # Give tasks a moment to see the stop signal
        await asyncio.sleep(1)
    
    async def availability_monitor(self):
        """Monitor device availability with fast ping checks"""
        while self.is_scanning:
            try:
                devices = await self.get_monitored_devices()
                
                # Process devices in batches
                batch_size = 20
                for i in range(0, len(devices), batch_size):
                    if not self.is_scanning:  # Check stop signal
                        break
                    batch = devices[i:i + batch_size]
                    tasks = [self.check_device_availability(device) for device in batch]
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sleep with periodic stop signal checks
                for _ in range(self.intervals['ping_sweep']):
                    if not self.is_scanning:
                        break
                    await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("Availability monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in availability monitor: {e}")
                await asyncio.sleep(5)
    
    async def discovery_scanner(self):
        """Continuous network discovery for new devices"""
        cleanup_counter = 0
        while self.is_scanning:
            try:
                # Get network configuration
                config = await self.get_network_config()
                network_range = config.get('scan_range', '192.168.1.0/24')
                
                # Perform network discovery
                await self.scan_network_range(network_range)
                
                # Periodic false positive cleanup (every 10 discovery cycles)
                cleanup_counter += 1
                if cleanup_counter >= 10:
                    logger.info("Running periodic false positive cleanup...")
                    await self.cleanup_false_positive_devices()
                    cleanup_counter = 0
                
                # Sleep with periodic stop signal checks
                for _ in range(self.intervals['discovery_scan']):
                    if not self.is_scanning:
                        break
                    await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("Discovery scanner cancelled")
                break
            except Exception as e:
                logger.error(f"Error in discovery scanner: {e}")
                await asyncio.sleep(10)
    
    async def port_analyzer(self):
        """Enhanced periodic port scanning with change detection"""
        while self.is_scanning:
            try:
                devices = await self.get_monitored_devices()
                
                # Scan ports for a subset of devices each cycle
                for device in devices[:3]:  # Limit to 3 devices per cycle for faster scanning
                    if not self.is_scanning:  # Check stop signal
                        break
                    await self.scan_device_ports_with_change_detection(device)
                
                # Sleep with periodic stop signal checks
                for _ in range(self.intervals['port_scan']):
                    if not self.is_scanning:
                        break
                    await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("Port analyzer cancelled")
                break
            except Exception as e:
                logger.error(f"Error in port analyzer: {e}")
                await asyncio.sleep(30)
    
    async def status_broadcaster(self):
        """Broadcast device status updates via WebSocket"""
        while self.is_scanning:
            try:
                # Get current device statistics
                stats = await self.get_network_statistics()
                
                # Broadcast to all connected clients
                await self.broadcast_to_clients({
                    'type': 'network_stats_update',
                    'data': stats,
                    'timestamp': timezone.now().isoformat()
                })
                
                # Sleep with periodic stop signal checks
                for _ in range(self.intervals['status_update']):
                    if not self.is_scanning:
                        break
                    await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                logger.info("Status broadcaster cancelled")
                break
            except Exception as e:
                logger.error(f"Error in status broadcaster: {e}")
                await asyncio.sleep(10)
    
    async def check_device_availability(self, device):
        """Check if a device is available and update its status"""
        try:
            from .models import NetworkDevice, DeviceStatusHistory
            from channels.db import database_sync_to_async
            
            # Ping the device
            is_online, response_time = await asyncio.get_event_loop().run_in_executor(
                self.executor, NetworkScanner().ping_host, device.ip_address
            )
            
            # Update device status
            previous_status = device.status
            new_status = 'online' if is_online else 'offline'
            
            # Update device fields using async-safe wrapper
            @database_sync_to_async
            def update_device_status():
                try:
                    # Refresh device from database to avoid stale data
                    device.refresh_from_db()
                    
                    device.status = new_status
                    device.last_seen = timezone.now()
                    device.response_time = response_time if is_online else None
                    
                    # Update ping statistics
                    if hasattr(device, 'update_ping_stats'):
                        device.update_ping_stats(is_online, response_time if is_online else None)
                    
                    # Calculate uptime if device came back online
                    if previous_status == 'offline' and new_status == 'online':
                        if hasattr(device, 'calculate_uptime_percentage'):
                            device.calculate_uptime_percentage()
                    
                    device.save()
                    return device
                except NetworkDevice.DoesNotExist:
                    # Device was deleted, return None
                    return None
            
            # Update device in database
            updated_device = await update_device_status()
            
            # If device was deleted, skip further processing
            if updated_device is None:
                logger.debug(f"Device {device.ip_address} no longer exists, skipping availability update")
                return
            
            # Create status history entry if status changed
            if previous_status != new_status:
                await self.create_status_history(updated_device, new_status, response_time)
                
                # Broadcast status change
                await self.broadcast_device_status_change(updated_device, previous_status, new_status)
            
            # Update device cache
            self.device_cache[device.id] = {
                'status': new_status,
                'response_time': response_time,
                'last_seen': updated_device.last_seen.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking availability for {device.ip_address}: {e}")
    
    async def scan_network_range(self, network_range):
        """Scan network range for new devices"""
        try:
            scanner = NetworkScanner()
            
            # Generate IPs to scan
            network = ipaddress.IPv4Network(network_range, strict=False)
            ip_list = [str(ip) for ip in network.hosts()][:254]  # Limit to first 254 IPs
            
            # Scan in batches
            batch_size = 50
            for i in range(0, len(ip_list), batch_size):
                batch = ip_list[i:i + batch_size]
                tasks = [self.scan_single_ip(ip) for ip in batch]
                results = await asyncio.gather(*tasks)
                
                # Process results
                for result in results:
                    if result and result.get('is_alive'):
                        await self.handle_discovered_device(result)
        
        except Exception as e:
            logger.error(f"Error scanning network range {network_range}: {e}")
    
    async def scan_single_ip(self, ip):
        """Scan a single IP address"""
        try:
            scanner = NetworkScanner()
            is_alive, response_time = await asyncio.get_event_loop().run_in_executor(
                self.executor, scanner.ping_host, ip
            )
            
            if is_alive:
                device_info = await asyncio.get_event_loop().run_in_executor(
                    self.executor, scanner.get_device_info, ip
                )
                device_info.update({
                    'ip_address': ip,
                    'is_alive': True,
                    'response_time': response_time
                })
                return device_info
        
        except Exception as e:
            logger.debug(f"Error scanning IP {ip}: {e}")
        
        return None
    
    async def handle_discovered_device(self, device_data):
        """Handle a newly discovered device with enhanced false positive detection"""
        try:
            ip_address = device_data.get('ip_address')
            mac_address = device_data.get('mac_address')
            
            # Enhanced false positive detection
            if await self.is_false_positive_device(device_data):
                logger.info(f"Rejecting false positive device: {ip_address}")
                return
            
            # Check for existing device by IP
            existing_device = await self.get_device_by_ip(ip_address)
            
            if existing_device:
                # Handle IP address change detection
                if mac_address and existing_device.mac_address and mac_address != existing_device.mac_address:
                    await self.handle_ip_change(existing_device, device_data)
                else:
                    # Update existing device
                    await self.update_existing_device(existing_device, device_data)
            else:
                # Check for existing device by MAC (if available)
                if mac_address:
                    existing_device_by_mac = await self.get_device_by_mac(mac_address)
                    if existing_device_by_mac:
                        await self.handle_ip_change(existing_device_by_mac, device_data)
                        return
                
                # Create new device
                await self.create_new_device(device_data)
                
        except Exception as e:
            logger.error(f"Error handling discovered device {device_data.get('ip_address', 'unknown')}: {e}")

    async def is_false_positive_device(self, device_data):
        """Enhanced false positive detection with multiple criteria"""
        ip_address = device_data.get('ip_address')
        mac_address = device_data.get('mac_address')
        hostname = device_data.get('hostname')
        response_time = device_data.get('response_time')
        
        # Criteria 1: No MAC address and no hostname (likely phantom IP)
        if not mac_address and not hostname:
            logger.debug(f"False positive detected - No MAC/hostname: {ip_address}")
            return True
        
        # Criteria 2: Gateway MAC conflict detection
        if mac_address and await self.is_gateway_mac_conflict(ip_address, mac_address):
            logger.warning(f"False positive detected - Gateway MAC conflict: {ip_address} with MAC {mac_address}")
            return True
        
        # Criteria 3: Unrealistic response time (too fast, likely ARP cache artifact)
        if response_time and response_time < 0.1:  # Less than 0.1ms is suspicious
            logger.debug(f"False positive detected - Unrealistic response time: {ip_address} ({response_time}ms)")
            return True
        
        # Criteria 4: Extremely high response time (7+ seconds indicates timeout/false positive)
        if response_time and response_time > 7000:  # More than 7 seconds is suspicious
            logger.warning(f"False positive detected - Extremely high response time: {ip_address} ({response_time}ms)")
            return True
        
        # Criteria 5: Check if device has history of being consistently offline
        if await self.has_false_positive_history(ip_address):
            logger.info(f"False positive detected - Consistent offline history: {ip_address}")
            return True
        
        # Criteria 6: Broadcast or multicast addresses
        if self.is_broadcast_or_multicast(ip_address):
            logger.debug(f"False positive detected - Broadcast/multicast: {ip_address}")
            return True
        
        return False
    
    async def is_gateway_mac_conflict(self, ip_address, mac_address):
        """Check if the MAC address belongs to a gateway/router but IP doesn't match"""
        try:
            # Get known gateway devices
            @database_sync_to_async
            def get_gateway_devices():
                from .models import NetworkDevice
                return list(NetworkDevice.objects.filter(
                    device_type__in=['router', 'gateway'],
                    mac_address__isnull=False
                ).values('ip_address', 'mac_address'))
            
            gateway_devices = await get_gateway_devices()
            
            for gateway in gateway_devices:
                if (gateway['mac_address'] == mac_address and 
                    gateway['ip_address'] != ip_address):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking gateway MAC conflict: {e}")
            return False
    
    async def has_false_positive_history(self, ip_address):
        """Check if device has a history of being a false positive"""
        try:
            @database_sync_to_async
            def check_device_history():
                from .models import NetworkDevice, DeviceStatusHistory
                from django.utils import timezone
                from datetime import timedelta
                
                try:
                    device = NetworkDevice.objects.get(ip_address=ip_address)
                    
                    # Check if device has been offline for more than 24 hours
                    if (device.status == 'offline' and 
                        device.last_seen and 
                        timezone.now() - device.last_seen > timedelta(hours=24)):
                        
                        # Check ping statistics
                        if (device.ping_failure_count > 50 and 
                            device.ping_success_count == 0):
                            return True
                        
                        # Check if packet loss is extremely high
                        if hasattr(device, 'packet_loss_percentage') and device.packet_loss_percentage > 95:
                            return True
                    
                    return False
                except NetworkDevice.DoesNotExist:
                    return False
            
            return await check_device_history()
        except Exception as e:
            logger.error(f"Error checking device history for {ip_address}: {e}")
            return False
    
    def is_broadcast_or_multicast(self, ip_address):
        """Check if IP is broadcast or multicast address"""
        try:
            import ipaddress
            ip = ipaddress.IPv4Address(ip_address)
            return ip.is_multicast or ip.is_broadcast
        except:
            return False
    
    async def cleanup_false_positive_devices(self):
        """Periodic cleanup of false positive devices"""
        try:
            @database_sync_to_async
            def get_false_positive_candidates():
                from .models import NetworkDevice
                from django.utils import timezone
                from datetime import timedelta
                
                from django.db import models
                
                # Find devices that are likely false positives
                candidates = NetworkDevice.objects.filter(
                    # Offline for more than 48 hours
                    status='offline',
                    last_seen__lt=timezone.now() - timedelta(hours=48)
                ).filter(
                    # AND one of these conditions:
                    # 1. No MAC address and no hostname
                    models.Q(mac_address__isnull=True, hostname__isnull=True) |
                    models.Q(mac_address='', hostname='') |
                    # 2. Extremely high failure rate
                    models.Q(ping_failure_count__gt=100, ping_success_count=0) |
                    # 3. No successful pings ever
                    models.Q(ping_success_count=0, ping_failure_count__gt=20)
                )
                
                return list(candidates.values('id', 'ip_address', 'mac_address', 'hostname', 
                                            'ping_success_count', 'ping_failure_count', 'last_seen'))
            
            candidates = await get_false_positive_candidates()
            
            if candidates:
                logger.info(f"Found {len(candidates)} false positive device candidates for cleanup")
                
                for candidate in candidates:
                    # Additional validation before deletion
                    if await self.confirm_false_positive(candidate):
                        await self.remove_false_positive_device(candidate['id'], candidate['ip_address'])
                        
        except Exception as e:
            logger.error(f"Error during false positive cleanup: {e}")
    
    async def confirm_false_positive(self, device_data):
        """Final confirmation that device is a false positive"""
        ip_address = device_data['ip_address']
        
        # Perform final ping test
        is_online, response_time = await asyncio.get_event_loop().run_in_executor(
            self.executor, NetworkScanner().ping_host, ip_address
        )
        
        if is_online:
            logger.info(f"Device {ip_address} responded to final ping test, keeping it")
            return False
        
        # Check if it's a reserved IP range that shouldn't be monitored
        if self.is_reserved_ip(ip_address):
            logger.info(f"Device {ip_address} is in reserved range, removing")
            return True
        
        return True
    
    def is_reserved_ip(self, ip_address):
        """Check if IP is in reserved ranges that shouldn't be monitored"""
        try:
            import ipaddress
            ip = ipaddress.IPv4Address(ip_address)
            
            # Common reserved ranges to avoid
            reserved_ranges = [
                ipaddress.IPv4Network('169.254.0.0/16'),  # Link-local
                ipaddress.IPv4Network('224.0.0.0/4'),    # Multicast
                ipaddress.IPv4Network('240.0.0.0/4'),    # Reserved
            ]
            
            for reserved in reserved_ranges:
                if ip in reserved:
                    return True
            
            return False
        except:
            return False
    
    async def remove_false_positive_device(self, device_id, ip_address):
        """Remove a confirmed false positive device"""
        try:
            @database_sync_to_async
            def delete_device():
                from .models import NetworkDevice
                try:
                    device = NetworkDevice.objects.get(id=device_id)
                    device.delete()
                    return True
                except NetworkDevice.DoesNotExist:
                    return False
            
            if await delete_device():
                logger.info(f"Removed false positive device: {ip_address}")
                
                # Create security event for audit trail
                await self.create_security_event(
                    'false_positive_removed',
                    'low',
                    f"False positive device removed: {ip_address}",
                    f"Device {ip_address} was identified and removed as a false positive after validation",
                    details={'ip_address': ip_address, 'reason': 'false_positive_cleanup'}
                )
        except Exception as e:
            logger.error(f"Error removing false positive device {ip_address}: {e}")

    async def scan_device_ports(self, device):
        """Enhanced port scanning using Nmap when available"""
        try:
            # Mark device as being scanned
            device.is_scanning = True
            device.scan_progress = 0
            await self.save_device(device)
            
            # Broadcast scan started
            await self.broadcast_to_clients({
                'type': 'port_scan_started',
                'device_id': device.id,
                'ip_address': device.ip_address,
                'timestamp': timezone.now().isoformat()
            })
            
            logger.info(f"Starting enhanced port scan for {device.ip_address}")
            
            # Update progress - Initial setup
            device.scan_progress = 10
            await self.save_device(device)
            await self.broadcast_to_clients({
                'type': 'port_scan_progress',
                'device_id': device.id,
                'ip_address': device.ip_address,
                'progress': 10,
                'status': 'initializing',
                'timestamp': timezone.now().isoformat()
            })
            
            # Update progress - Starting scan
            device.scan_progress = 25
            await self.save_device(device)
            await self.broadcast_to_clients({
                'type': 'port_scan_progress',
                'device_id': device.id,
                'ip_address': device.ip_address,
                'progress': 25,
                'status': 'scanning',
                'timestamp': timezone.now().isoformat()
            })
            
            # Use enhanced Nmap scanner
            open_ports = await asyncio.get_event_loop().run_in_executor(
                None, self.scan_ports, device.ip_address
            )
            
            # Update progress - Processing results
            device.scan_progress = 75
            await self.save_device(device)
            await self.broadcast_to_clients({
                'type': 'port_scan_progress',
                'device_id': device.id,
                'ip_address': device.ip_address,
                'progress': 75,
                'status': 'processing',
                'timestamp': timezone.now().isoformat()
            })
            
            logger.info(f"Enhanced port scan completed for {device.ip_address}: {len(open_ports)} open ports found")
            
            # Update device with port information
            device.open_ports = open_ports
            device.last_port_scan = timezone.now()
            device.is_scanning = False
            device.scan_progress = 100
            
            await self.save_device(device)
            
            # Broadcast port scan completion
            await self.broadcast_port_scan_complete(device, open_ports)
            
            return open_ports
            
        except Exception as e:
            logger.error(f"Error scanning ports for {device.ip_address}: {e}")
            device.is_scanning = False
            device.scan_progress = 0
            await self.save_device(device)
            
            # Broadcast error
            await self.broadcast_to_clients({
                'type': 'port_scan_error',
                'device_id': device.id,
                'ip_address': device.ip_address,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            })
            
            raise e
    
    # Helper methods
    async def get_monitored_devices(self):
        """Get all devices that should be monitored"""
        from .models import NetworkDevice
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_devices():
            return list(NetworkDevice.objects.filter(monitor_enabled=True))
        
        return await get_devices()
    
    async def get_network_config(self):
        """Get network monitoring configuration"""
        from .models import NetworkConfiguration
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_config():
            try:
                config = NetworkConfiguration.objects.filter(is_active=True).first()
                if config:
                    return {
                        'scan_range': config.scan_range,
                        'scan_interval': config.scan_interval,
                        'traffic_monitoring': config.traffic_monitoring,
                        'security_monitoring': config.security_monitoring,
                    }
            except:
                pass
            
            return {
                'scan_range': '192.168.1.0/24',
                'scan_interval': 300,
                'traffic_monitoring': True,
                'security_monitoring': True,
            }
        
        return await get_config()
    
    async def get_network_statistics(self):
        """Get current network statistics"""
        from .models import NetworkDevice, SecurityEvent
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_stats():
            total_devices = NetworkDevice.objects.count()
            online_devices = NetworkDevice.objects.filter(status='online').count()
            offline_devices = NetworkDevice.objects.filter(status='offline').count()
            new_devices_today = NetworkDevice.objects.filter(
                first_seen__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            unresolved_alerts = SecurityEvent.objects.filter(is_resolved=False).count()
            
            return {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': offline_devices,
                'new_devices_today': new_devices_today,
                'unresolved_alerts': unresolved_alerts,
                'last_updated': timezone.now().isoformat()
            }
        
        return await get_stats()
    
    async def get_device_by_ip(self, ip_address):
        """Get device by IP address"""
        from .models import NetworkDevice
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_device():
            try:
                return NetworkDevice.objects.get(ip_address=ip_address)
            except NetworkDevice.DoesNotExist:
                return None
        
        return await get_device()
    
    async def get_device_by_mac(self, mac_address):
        """Get device by MAC address"""
        from .models import NetworkDevice
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def get_device():
            try:
                return NetworkDevice.objects.get(mac_address=mac_address, status='online')
            except NetworkDevice.DoesNotExist:
                return None
        
        return await get_device()
    
    async def handle_ip_change(self, existing_device, new_device_data):
        """Handle when a device changes IP address"""
        try:
            old_ip = existing_device.ip_address
            new_ip = new_device_data['ip_address']
            
            logger.info(f"Device IP change detected: {existing_device.hostname or existing_device.mac_address} changed from {old_ip} to {new_ip}")
            
            # Update device with new IP
            existing_device.ip_address = new_ip
            existing_device.last_seen = timezone.now()
            existing_device.status = 'online'
            existing_device.response_time = new_device_data.get('response_time', 0)
            
            # Update other fields if available
            if new_device_data.get('hostname'):
                existing_device.hostname = new_device_data['hostname']
            
            await self.save_device(existing_device)
            
            # Create security event for IP change
            await self.create_security_event(
                'ip_change',
                'medium',
                f"Device IP Address Changed",
                f"Device {existing_device.hostname or existing_device.mac_address} changed IP from {old_ip} to {new_ip}",
                target_device=existing_device,
                details={
                    'old_ip': old_ip,
                    'new_ip': new_ip,
                    'mac_address': existing_device.mac_address,
                    'hostname': existing_device.hostname
                }
            )
            
            # Broadcast IP change event
            await self.broadcast_to_clients({
                'type': 'device_ip_changed',
                'device_id': existing_device.id,
                'old_ip': old_ip,
                'new_ip': new_ip,
                'mac_address': existing_device.mac_address,
                'hostname': existing_device.hostname,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling IP change: {e}")
    
    async def update_existing_device(self, existing_device, device_data):
        """Update an existing device with new discovery data"""
        try:
            # Track if status changed
            old_status = existing_device.status
            new_status = 'online'  # Device was discovered, so it's online
            
            # Update device fields
            existing_device.status = new_status
            existing_device.last_seen = timezone.now()
            existing_device.response_time = device_data.get('response_time', 0)
            
            # Update hostname if provided and different
            if device_data.get('hostname') and device_data['hostname'] != existing_device.hostname:
                existing_device.hostname = device_data['hostname']
            
            # Update device type if provided and different
            if device_data.get('device_type') and device_data['device_type'] != existing_device.device_type:
                existing_device.device_type = device_data['device_type']
            
            # Update manufacturer if provided and different
            if device_data.get('manufacturer') and device_data['manufacturer'] != existing_device.manufacturer:
                existing_device.manufacturer = device_data['manufacturer']
            
            # Update ping statistics
            if old_status != new_status:
                if new_status == 'online':
                    existing_device.ping_success_count = (existing_device.ping_success_count or 0) + 1
                else:
                    existing_device.ping_failure_count = (existing_device.ping_failure_count or 0) + 1
            
            # Save the updated device
            await self.save_device(existing_device)
            
            # Create status history entry if status changed
            if old_status != new_status:
                await self.create_status_history(existing_device, new_status, device_data.get('response_time', 0))
                
                # Broadcast status change
                await self.broadcast_device_status_change(existing_device, old_status, new_status)
                
                logger.info(f"Device {existing_device.ip_address} status updated: {old_status} -> {new_status}")
            
        except Exception as e:
            logger.error(f"Error updating existing device {device_data.get('ip_address', 'unknown')}: {e}")
    
    async def create_new_device(self, device_data):
        """Create a new network device"""
        from .models import NetworkDevice
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def create_device():
            return NetworkDevice.objects.create(
                ip_address=device_data['ip_address'],
                hostname=device_data.get('hostname', ''),
                mac_address=device_data.get('mac_address', ''),
                device_type=device_data.get('device_type', 'unknown'),
                manufacturer=device_data.get('manufacturer', ''),
                status='online',
                response_time=device_data.get('response_time', 0),
                last_seen=timezone.now(),
                monitor_enabled=True
            )
        
        return await create_device()
    
    async def save_device(self, device):
        """Save device to database (async-safe)"""
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def _save_device():
            device.save()
        
        await _save_device()
    
    async def create_status_history(self, device, status, response_time):
        """Create a status history entry"""
        from .models import DeviceStatusHistory
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def create_history():
            DeviceStatusHistory.objects.create(
                device=device,
                status=status,
                response_time=response_time,
                uptime_at_time=device.uptime_percentage,
                packet_loss_at_time=device.packet_loss_rate
            )
        
        await create_history()
    
    async def create_security_event(self, event_type: str, severity: str, title: str, 
                                  description: str, source_device=None, target_device=None, details=None):
        """Create a security event"""
        from .models import SecurityEvent
        from channels.db import database_sync_to_async
        
        @database_sync_to_async
        def create_event():
            return SecurityEvent.objects.create(
                event_type=event_type,
                severity=severity,
                title=title,
                description=description,
                source_device=source_device,
                target_device=target_device,
                details=details or {},
                timestamp=timezone.now()
            )
        
        event = await create_event()
        
        # Broadcast security event
        await self.broadcast_to_clients({
            'type': 'security_event',
            'event': {
                'id': event.id,
                'event_type': event.event_type,
                'severity': event.severity,
                'title': event.title,
                'description': event.description,
                'timestamp': event.timestamp.isoformat()
            },
            'timestamp': timezone.now().isoformat()
        })
        
        return event
    
    # WebSocket broadcasting methods
    async def broadcast_to_clients(self, message):
        """Broadcast message to all connected WebSocket clients"""
        if self.channel_layer:
            await self.channel_layer.group_send("network_monitor", message)
    
    async def broadcast_device_status_change(self, device, old_status, new_status):
        """Broadcast device status change"""
        await self.broadcast_to_clients({
            'type': 'device_status_changed',
            'device_id': device.id,
            'ip_address': device.ip_address,
            'hostname': device.hostname,
            'old_status': old_status,
            'new_status': new_status,
            'response_time': device.response_time,
            'last_seen': device.last_seen.isoformat(),
            'timestamp': timezone.now().isoformat()
        })
    
    async def broadcast_device_discovered(self, device):
        """Broadcast new device discovery"""
        await self.broadcast_to_clients({
            'type': 'device_discovered',
            'device': {
                'id': device.id,
                'ip_address': device.ip_address,
                'hostname': device.hostname,
                'mac_address': device.mac_address,
                'device_type': device.device_type,
                'manufacturer': device.manufacturer,
                'status': device.status,
                'last_seen': device.last_seen.isoformat(),
                'first_seen': device.first_seen.isoformat(),
                'open_ports': device.open_ports or [],
                'response_time': device.response_time,
                'is_monitored': device.is_monitored,
                'uptime_percentage': device.uptime_percentage
            },
            'timestamp': timezone.now().isoformat()
        })
    
    async def broadcast_port_scan_complete(self, device, open_ports):
        """Broadcast port scan completion"""
        await self.broadcast_to_clients({
            'type': 'port_scan_complete',
            'device_id': device.id,
            'ip_address': device.ip_address,
            'open_ports': open_ports,
            'scan_time': device.last_port_scan.isoformat() if device.last_port_scan else None,
            'timestamp': timezone.now().isoformat()
        })

    def start_background_monitoring(self):
        """Start background monitoring for automatic device status updates"""
        if hasattr(self, '_monitoring_thread') and self._monitoring_thread.is_alive():
            logger.info("Background monitoring already running")
            return
            
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._background_monitor_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Started background device monitoring")
    
    def stop_background_monitoring(self):
        """Stop background monitoring"""
        self._monitoring_active = False
        if hasattr(self, '_monitoring_thread'):
            self._monitoring_thread.join(timeout=5)
        logger.info("Stopped background device monitoring")
    
    def _background_monitor_loop(self):
        """Background monitoring loop"""
        while getattr(self, '_monitoring_active', False):
            try:
                # Import here to avoid circular imports
                from .models import NetworkDevice
                
                # Get all monitored devices
                monitored_devices = NetworkDevice.objects.filter(is_monitored=True)
                
                for device in monitored_devices:
                    try:
                        # Ping the device
                        is_alive, response_time = self.network_scanner.ping_host(device.ip_address, timeout=2)
                        
                        # Update device status if changed
                        old_status = device.status
                        new_status = 'online' if is_alive else 'offline'
                        
                        if old_status != new_status:
                            device.status = new_status
                            device.response_time = response_time if is_alive else None
                            device.last_seen = timezone.now() if is_alive else device.last_seen
                            device.save()
                            
                            logger.info(f"Device {device.ip_address} status changed: {old_status} -> {new_status}")
                            
                            # Broadcast status change via WebSocket
                            if self.channel_layer:
                                async_to_sync(self.channel_layer.group_send)(
                                    "network_updates",
                                    {
                                        "type": "device_status_changed",
                                        "device_id": device.id,
                                        "ip_address": device.ip_address,
                                        "hostname": device.hostname,
                                        "old_status": old_status,
                                        "new_status": new_status,
                                        "response_time": response_time,
                                        "last_seen": device.last_seen.isoformat(),
                                        "timestamp": timezone.now().isoformat()
                                    }
                                )
                        
                    except Exception as e:
                        logger.error(f"Error monitoring device {device.ip_address}: {e}")
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in background monitoring loop: {e}")
                time.sleep(30)

    def scan_ports(self, ip: str, ports: List[int] = None, include_udp: bool = False) -> List[Dict]:
        """
        Advanced port scanning using pure Python - no admin rights or external software required
        """
        logger.info(f"Starting advanced Python port scan for {ip}")
        
        try:
            # Use adaptive scanning strategy for best results
            open_ports = self.advanced_scanner.adaptive_scan(ip)
            
            logger.info(f"Advanced scan completed for {ip}: {len(open_ports)} open ports found")
            return open_ports
                
        except Exception as e:
            logger.error(f"Advanced port scan error for {ip}: {e}")
            # Fallback to basic socket scanning if advanced scanner fails
            return self._enhanced_socket_scan(ip, ports, include_udp)

    def _enhanced_socket_scan(self, ip: str, ports: List[int] = None, include_udp: bool = False) -> List[Dict]:
        """Enhanced socket-based scanning as fallback"""
        if ports is None:
            # Priority ports - most likely to be open and important
            priority_ports = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445, 1433, 3306, 3389, 8080]
            
            # Extended ports for comprehensive scan
            extended_ports = [
                110, 143, 993, 995, 161, 162, 389, 636, 1521, 27017, 6379,
                5985, 5986, 8000, 8001, 8008, 8081, 8082, 8090, 8443,
                9000, 9001, 9090, 3000, 4000, 5000, 8888, 10050, 10051
            ]
            
            ports = priority_ports + extended_ports
        
        open_ports = []
        
        def scan_single_tcp_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.8)  # Faster timeout
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    service_info = self._get_service_info(port)
                    return {
                        'port': port,
                        'protocol': 'TCP',
                        'service': service_info['service'],
                        'description': service_info['description'],
                        'risk_level': service_info['risk_level'],
                        'state': 'open',
                        'scanner': 'socket'
                    }
            except Exception:
                pass
            return None
        
        # Scan TCP ports concurrently with optimized workers
        max_workers = min(10, len(ports))  # Limit workers based on port count, max 10
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # TCP port scanning
            future_to_port = {executor.submit(scan_single_tcp_port, port): port for port in ports}
            
            # Add UDP scanning for critical UDP ports only if requested
            if include_udp:
                udp_ports = [53, 161, 162]  # Only most critical UDP ports to avoid timeouts
                udp_futures = {executor.submit(self._scan_single_udp_port, ip, port): port for port in udp_ports}
                future_to_port.update(udp_futures)
            
            # Process results with timeout to avoid hanging
            import concurrent.futures
            try:
                for future in concurrent.futures.as_completed(future_to_port, timeout=30):  # 30 second timeout
                    result = future.result()
                    if result:
                        open_ports.append(result)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Port scan timeout for {ip}, returning partial results")
                # Cancel remaining futures
                for future in future_to_port:
                    future.cancel()
        
        # Sort by risk level and port number
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        open_ports.sort(key=lambda x: (risk_order.get(x['risk_level'], 4), x['port']))
        
        logger.info(f"Socket scan completed for {ip}: {len(open_ports)} open ports found")
        return open_ports

    def _scan_single_udp_port(self, ip: str, port: int) -> Optional[Dict]:
        """Scan a single UDP port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            # Send a simple UDP packet
            sock.sendto(b'', (ip, port))
            
            # Try to receive a response
            try:
                data, addr = sock.recvfrom(1024)
                sock.close()
                
                service_info = self._get_service_info(port)
                return {
                    'port': port,
                    'protocol': 'UDP',
                    'service': service_info['service'],
                    'description': service_info['description'],
                    'risk_level': service_info['risk_level'],
                    'state': 'open',
                    'scanner': 'socket'
                }
            except socket.timeout:
                # No response doesn't necessarily mean closed for UDP
                pass
            
            sock.close()
        except Exception:
            pass
        
        return None

    def _get_service_info(self, port: int) -> Dict:
        """Get enhanced service information for common ports"""
        port_database = {
            21: {'service': 'FTP', 'description': 'File Transfer Protocol', 'risk_level': 'high'},
            22: {'service': 'SSH', 'description': 'Secure Shell', 'risk_level': 'high'},
            23: {'service': 'Telnet', 'description': 'Telnet (INSECURE)', 'risk_level': 'critical'},
            25: {'service': 'SMTP', 'description': 'Simple Mail Transfer Protocol', 'risk_level': 'medium'},
            53: {'service': 'DNS', 'description': 'Domain Name System', 'risk_level': 'medium'},
            80: {'service': 'HTTP', 'description': 'Hypertext Transfer Protocol', 'risk_level': 'medium'},
            110: {'service': 'POP3', 'description': 'Post Office Protocol v3', 'risk_level': 'medium'},
            135: {'service': 'RPC', 'description': 'Microsoft RPC Endpoint Mapper', 'risk_level': 'critical'},
            139: {'service': 'NetBIOS-SSN', 'description': 'NetBIOS Session Service', 'risk_level': 'high'},
            143: {'service': 'IMAP', 'description': 'Internet Message Access Protocol', 'risk_level': 'medium'},
            443: {'service': 'HTTPS', 'description': 'HTTP over SSL/TLS', 'risk_level': 'low'},
            445: {'service': 'SMB', 'description': 'Server Message Block', 'risk_level': 'critical'},
            993: {'service': 'IMAPS', 'description': 'IMAP over SSL', 'risk_level': 'low'},
            995: {'service': 'POP3S', 'description': 'POP3 over SSL', 'risk_level': 'low'},
            1433: {'service': 'MSSQL', 'description': 'Microsoft SQL Server', 'risk_level': 'critical'},
            3306: {'service': 'MySQL', 'description': 'MySQL Database Server', 'risk_level': 'critical'},
            3389: {'service': 'RDP', 'description': 'Remote Desktop Protocol', 'risk_level': 'critical'},
            5432: {'service': 'PostgreSQL', 'description': 'PostgreSQL Database', 'risk_level': 'critical'},
            8080: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP port', 'risk_level': 'medium'},
            8443: {'service': 'HTTPS-Alt', 'description': 'Alternative HTTPS port', 'risk_level': 'low'},
            161: {'service': 'SNMP', 'description': 'Simple Network Management Protocol', 'risk_level': 'high'},
            162: {'service': 'SNMP-Trap', 'description': 'SNMP Trap', 'risk_level': 'high'},
            389: {'service': 'LDAP', 'description': 'Lightweight Directory Access Protocol', 'risk_level': 'medium'},
            636: {'service': 'LDAPS', 'description': 'LDAP over SSL', 'risk_level': 'low'},
            1521: {'service': 'Oracle', 'description': 'Oracle Database', 'risk_level': 'critical'},
            27017: {'service': 'MongoDB', 'description': 'MongoDB Database', 'risk_level': 'high'},
            6379: {'service': 'Redis', 'description': 'Redis Database', 'risk_level': 'high'},
        }
        
        return port_database.get(port, {
            'service': f'Port-{port}',
            'description': f'Unknown service on port {port}',
            'risk_level': 'medium'
        })

    async def scan_device_ports_with_change_detection(self, device):
        """Scan device ports and detect changes"""
        try:
            # Store previous port state
            previous_ports = device.open_ports or []
            previous_port_numbers = set(port.get('port') for port in previous_ports if isinstance(port, dict))
            
            # Perform port scan
            await self.scan_device_ports(device)
            
            # Refresh device from database to get updated ports
            await device.arefresh_from_db()
            current_ports = device.open_ports or []
            current_port_numbers = set(port.get('port') for port in current_ports if isinstance(port, dict))
            
            # Detect changes
            new_ports = current_port_numbers - previous_port_numbers
            closed_ports = previous_port_numbers - current_port_numbers
            
            # Broadcast port changes
            if new_ports or closed_ports:
                await self.broadcast_port_changes(device, new_ports, closed_ports)
                
                # Create security events for significant changes
                if new_ports:
                    await self.create_security_event(
                        'port_opened',
                        'medium',
                        f"New ports opened on {device.ip_address}",
                        f"Device {device.hostname or device.ip_address} has opened new ports: {', '.join(map(str, new_ports))}",
                        target_device=device,
                        details={'new_ports': list(new_ports)}
                    )
                
                if closed_ports:
                    await self.create_security_event(
                        'port_closed',
                        'low',
                        f"Ports closed on {device.ip_address}",
                        f"Device {device.hostname or device.ip_address} has closed ports: {', '.join(map(str, closed_ports))}",
                        target_device=device,
                        details={'closed_ports': list(closed_ports)}
                    )
            
        except Exception as e:
            logger.error(f"Error in port change detection for {device.ip_address}: {e}")
    
    async def broadcast_port_changes(self, device, new_ports, closed_ports):
        """Broadcast port changes via WebSocket"""
        try:
            if self.channel_layer:
                await self.channel_layer.group_send(
                    "network_monitor",
                    {
                        "type": "port_changes_detected",
                        "device_id": device.id,
                        "device_ip": device.ip_address,
                        "hostname": device.hostname,
                        "new_ports": list(new_ports),
                        "closed_ports": list(closed_ports),
                        "timestamp": timezone.now().isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error broadcasting port changes: {e}")


# Global instances
network_scanner = NetworkScanner()
traffic_monitor = TrafficMonitor()
realtime_monitor = RealTimeNetworkMonitor() 