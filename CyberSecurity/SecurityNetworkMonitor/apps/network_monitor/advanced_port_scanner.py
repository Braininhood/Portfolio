#!/usr/bin/env python
"""
Advanced Pure Python Port Scanner
No external dependencies, no admin rights required, more reliable than basic socket scanning
"""
import socket
import threading
import time
import struct
import select
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import ipaddress

logger = logging.getLogger(__name__)

class AdvancedPortScanner:
    """
    Advanced port scanner using pure Python
    Features:
    - Multi-threaded scanning with optimized timeouts
    - Service banner grabbing for identification
    - Smart port prioritization
    - Connection state analysis
    - No external dependencies or admin rights required
    """
    
    def __init__(self):
        self.common_ports = self._get_common_ports()
        self.service_signatures = self._get_service_signatures()
        self.scan_timeout = 1.0
        self.banner_timeout = 2.0
        self.max_workers = 50  # Optimized for speed
        
    def _get_common_ports(self) -> Dict[int, Dict]:
        """Get common ports with service information - TCP and UDP"""
        return {
            # Web Services (TCP)
            80: {'service': 'HTTP', 'description': 'Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            443: {'service': 'HTTPS', 'description': 'Secure Web Server', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            8080: {'service': 'HTTP-Alt', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            8443: {'service': 'HTTPS-Alt', 'description': 'Alternative Secure Web', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            8000: {'service': 'HTTP-Dev', 'description': 'Development Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            8001: {'service': 'HTTP-Alt2', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            8008: {'service': 'HTTP-Alt3', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            8081: {'service': 'HTTP-Proxy', 'description': 'HTTP Proxy Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            8082: {'service': 'HTTP-Alt4', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            8090: {'service': 'HTTP-Alt5', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            3000: {'service': 'Node.js', 'description': 'Node.js Application', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            4000: {'service': 'HTTP-Dev2', 'description': 'Development Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            5000: {'service': 'HTTP-Dev3', 'description': 'Development Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            9000: {'service': 'HTTP-Alt6', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            9001: {'service': 'HTTP-Alt7', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            9090: {'service': 'HTTP-Alt8', 'description': 'Alternative Web Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            
            # Remote Access (TCP)
            22: {'service': 'SSH', 'description': 'Secure Shell', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            23: {'service': 'Telnet', 'description': 'Telnet (INSECURE)', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            3389: {'service': 'RDP', 'description': 'Remote Desktop', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            5985: {'service': 'WinRM-HTTP', 'description': 'Windows Remote Management', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            5986: {'service': 'WinRM-HTTPS', 'description': 'Windows Remote Management SSL', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            512: {'service': 'rexec', 'description': 'Remote Execution (INSECURE)', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            513: {'service': 'rlogin', 'description': 'Remote Login (INSECURE)', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            514: {'service': 'rsh', 'description': 'Remote Shell (INSECURE)', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            
            # File Transfer (TCP)
            21: {'service': 'FTP', 'description': 'File Transfer Protocol', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            20: {'service': 'FTP-Data', 'description': 'FTP Data Transfer', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            69: {'service': 'TFTP', 'description': 'Trivial File Transfer', 'risk': 'high', 'banner': False, 'protocol': 'udp'},
            115: {'service': 'SFTP', 'description': 'Simple File Transfer', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            989: {'service': 'FTPS-Data', 'description': 'FTP over SSL Data', 'risk': 'medium', 'banner': False, 'protocol': 'tcp'},
            990: {'service': 'FTPS', 'description': 'FTP over SSL', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            
            # Email (TCP)
            25: {'service': 'SMTP', 'description': 'Mail Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            110: {'service': 'POP3', 'description': 'Mail Retrieval', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            143: {'service': 'IMAP', 'description': 'Mail Access', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            465: {'service': 'SMTPS', 'description': 'Secure Mail Server', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            587: {'service': 'SMTP-Sub', 'description': 'Mail Submission', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            993: {'service': 'IMAPS', 'description': 'Secure Mail Access', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            995: {'service': 'POP3S', 'description': 'Secure Mail Retrieval', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            
            # Windows Networking (TCP/UDP)
            135: {'service': 'RPC', 'description': 'Windows RPC Endpoint Mapper', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            137: {'service': 'NetBIOS-NS', 'description': 'NetBIOS Name Service', 'risk': 'high', 'banner': False, 'protocol': 'udp'},
            138: {'service': 'NetBIOS-DGM', 'description': 'NetBIOS Datagram Service', 'risk': 'high', 'banner': False, 'protocol': 'udp'},
            139: {'service': 'NetBIOS-SSN', 'description': 'NetBIOS Session Service', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            445: {'service': 'SMB', 'description': 'Windows File Sharing', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            
            # Databases (TCP)
            1433: {'service': 'MSSQL', 'description': 'Microsoft SQL Server', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            1434: {'service': 'MSSQL-Mon', 'description': 'MSSQL Monitor', 'risk': 'critical', 'banner': False, 'protocol': 'udp'},
            3306: {'service': 'MySQL', 'description': 'MySQL Database', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            5432: {'service': 'PostgreSQL', 'description': 'PostgreSQL Database', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            1521: {'service': 'Oracle', 'description': 'Oracle Database', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            1522: {'service': 'Oracle-TNS', 'description': 'Oracle TNS Listener', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            27017: {'service': 'MongoDB', 'description': 'MongoDB Database', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            27018: {'service': 'MongoDB-Shard', 'description': 'MongoDB Shard Server', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            27019: {'service': 'MongoDB-Config', 'description': 'MongoDB Config Server', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            6379: {'service': 'Redis', 'description': 'Redis Database', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            11211: {'service': 'Memcached', 'description': 'Memcached Cache', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            9200: {'service': 'Elasticsearch', 'description': 'Elasticsearch Database', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            9300: {'service': 'Elasticsearch-Node', 'description': 'Elasticsearch Node Communication', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            
            # Network Services (TCP/UDP)
            53: {'service': 'DNS', 'description': 'Domain Name System', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            161: {'service': 'SNMP', 'description': 'Network Management', 'risk': 'high', 'banner': False, 'protocol': 'udp'},
            162: {'service': 'SNMP-Trap', 'description': 'SNMP Notifications', 'risk': 'high', 'banner': False, 'protocol': 'udp'},
            123: {'service': 'NTP', 'description': 'Network Time Protocol', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            67: {'service': 'DHCP-Server', 'description': 'DHCP Server', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            68: {'service': 'DHCP-Client', 'description': 'DHCP Client', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            
            # Directory Services (TCP)
            389: {'service': 'LDAP', 'description': 'Directory Service', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            636: {'service': 'LDAPS', 'description': 'Secure Directory Service', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            88: {'service': 'Kerberos', 'description': 'Kerberos Authentication', 'risk': 'medium', 'banner': False, 'protocol': 'tcp'},
            464: {'service': 'Kerberos-Pwd', 'description': 'Kerberos Password Change', 'risk': 'medium', 'banner': False, 'protocol': 'tcp'},
            
            # VPN & Tunneling (TCP/UDP)
            1723: {'service': 'PPTP', 'description': 'VPN Service', 'risk': 'medium', 'banner': False, 'protocol': 'tcp'},
            1194: {'service': 'OpenVPN', 'description': 'VPN Service', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            500: {'service': 'IKE', 'description': 'Internet Key Exchange', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            4500: {'service': 'IPSec-NAT', 'description': 'IPSec NAT Traversal', 'risk': 'medium', 'banner': False, 'protocol': 'udp'},
            
            # Vulnerable/Legacy Services (TCP)
            79: {'service': 'Finger', 'description': 'User Information (INSECURE)', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            111: {'service': 'RPC', 'description': 'Remote Procedure Call', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            515: {'service': 'LPD', 'description': 'Line Printer Daemon', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            540: {'service': 'UUCP', 'description': 'Unix-to-Unix Copy', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            1900: {'service': 'UPnP', 'description': 'Universal Plug and Play', 'risk': 'high', 'banner': False, 'protocol': 'udp'},
            
            # Industrial/IoT (TCP/UDP)
            102: {'service': 'S7', 'description': 'Siemens S7 Protocol', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            502: {'service': 'Modbus', 'description': 'Modbus Protocol', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            2404: {'service': 'IEC-104', 'description': 'IEC 60870-5-104', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            44818: {'service': 'EtherNet/IP', 'description': 'EtherNet/IP Protocol', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            20000: {'service': 'DNP3', 'description': 'DNP3 Protocol', 'risk': 'critical', 'banner': False, 'protocol': 'tcp'},
            
            # Monitoring & Management (TCP)
            10050: {'service': 'Zabbix-Agent', 'description': 'Zabbix Monitoring Agent', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            10051: {'service': 'Zabbix-Server', 'description': 'Zabbix Monitoring Server', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            5666: {'service': 'NRPE', 'description': 'Nagios Remote Plugin Executor', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            
            # Container & Virtualization (TCP)
            2375: {'service': 'Docker', 'description': 'Docker Daemon (INSECURE)', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            2376: {'service': 'Docker-SSL', 'description': 'Docker Daemon SSL', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            2377: {'service': 'Docker-Swarm', 'description': 'Docker Swarm', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            6443: {'service': 'Kubernetes', 'description': 'Kubernetes API Server', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            10250: {'service': 'Kubelet', 'description': 'Kubernetes Kubelet', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            
            # Gaming & Media (TCP/UDP)
            25565: {'service': 'Minecraft', 'description': 'Minecraft Server', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            27015: {'service': 'Steam', 'description': 'Steam Game Server', 'risk': 'low', 'banner': False, 'protocol': 'udp'},
            
            # Backup & File Sync (TCP)
            873: {'service': 'rsync', 'description': 'Remote Sync', 'risk': 'medium', 'banner': True, 'protocol': 'tcp'},
            2049: {'service': 'NFS', 'description': 'Network File System', 'risk': 'high', 'banner': False, 'protocol': 'tcp'},
            
            # Additional Vulnerable Ports
            1433: {'service': 'MSSQL', 'description': 'Microsoft SQL Server', 'risk': 'critical', 'banner': True, 'protocol': 'tcp'},
            5060: {'service': 'SIP', 'description': 'Session Initiation Protocol', 'risk': 'medium', 'banner': True, 'protocol': 'udp'},
            5061: {'service': 'SIP-TLS', 'description': 'SIP over TLS', 'risk': 'low', 'banner': True, 'protocol': 'tcp'},
            6000: {'service': 'X11', 'description': 'X Window System', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
            7001: {'service': 'Cassandra', 'description': 'Cassandra Database', 'risk': 'high', 'banner': True, 'protocol': 'tcp'},
        }
    
    def _get_service_signatures(self) -> Dict[str, str]:
        """Service identification signatures from banners"""
        return {
            'SSH-': 'SSH',
            'HTTP/': 'HTTP',
            'FTP': 'FTP',
            'SMTP': 'SMTP',
            'POP3': 'POP3',
            'IMAP': 'IMAP',
            'MySQL': 'MySQL',
            'PostgreSQL': 'PostgreSQL',
            'Microsoft SQL Server': 'MSSQL',
            'Oracle': 'Oracle',
            'MongoDB': 'MongoDB',
            'Redis': 'Redis',
            'Apache': 'Apache HTTP',
            'nginx': 'Nginx HTTP',
            'IIS': 'Microsoft IIS',
            'OpenSSH': 'OpenSSH',
            'Postfix': 'Postfix SMTP',
            'Dovecot': 'Dovecot Mail',
            'ProFTPD': 'ProFTPD',
            'vsftpd': 'vsftpd FTP',
        }
    
    def scan_port(self, ip: str, port: int, protocol: str = None) -> Optional[Dict]:
        """
        Scan a single port with advanced techniques (TCP/UDP)
        Returns port info if open, None if closed
        """
        # Determine protocol from port info or use default
        service_info = self.common_ports.get(port, {})
        if protocol is None:
            protocol = service_info.get('protocol', 'tcp')
        
        if protocol.lower() == 'udp':
            return self._scan_udp_port(ip, port)
        else:
            return self._scan_tcp_port(ip, port)
    
    def _scan_tcp_port(self, ip: str, port: int) -> Optional[Dict]:
        """Scan TCP port"""
        try:
            # Create socket with optimized settings
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.scan_timeout)
            
            # Enable socket reuse to avoid "Address already in use" errors
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Attempt connection
            start_time = time.time()
            result = sock.connect_ex((ip, port))
            connect_time = time.time() - start_time
            
            if result == 0:  # Port is open
                port_info = {
                    'port': port,
                    'protocol': 'TCP',
                    'state': 'open',
                    'response_time': round(connect_time * 1000, 2),  # ms
                    'scanner': 'advanced_python'
                }
                
                # Get service information
                service_info = self.common_ports.get(port, {
                    'service': f'Port-{port}',
                    'description': f'Unknown TCP service on port {port}',
                    'risk': 'medium',
                    'banner': False,
                    'protocol': 'tcp'
                })
                
                port_info.update({
                    'service': service_info['service'],
                    'description': service_info['description'],
                    'risk_level': service_info['risk']
                })
                
                # Try to grab banner for service identification
                if service_info.get('banner', False):
                    banner = self._grab_banner(sock, port)
                    if banner:
                        port_info['banner'] = banner
                        # Try to identify service from banner
                        identified_service = self._identify_service_from_banner(banner)
                        if identified_service:
                            port_info['service'] = identified_service
                            port_info['identified'] = True
                
                sock.close()
                return port_info
            else:
                sock.close()
                return None
                
        except socket.timeout:
            try:
                sock.close()
            except:
                pass
            return None
        except Exception as e:
            try:
                sock.close()
            except:
                pass
            return None
    
    def _scan_udp_port(self, ip: str, port: int) -> Optional[Dict]:
        """Scan UDP port using various techniques"""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.scan_timeout)
            
            start_time = time.time()
            
            # Send UDP probe based on service
            probe_data = self._get_udp_probe(port)
            sock.sendto(probe_data, (ip, port))
            
            try:
                # Try to receive response
                data, addr = sock.recvfrom(1024)
                connect_time = time.time() - start_time
                
                # Port is open and responding
                port_info = {
                    'port': port,
                    'protocol': 'UDP',
                    'state': 'open',
                    'response_time': round(connect_time * 1000, 2),
                    'scanner': 'advanced_python'
                }
                
                # Get service information
                service_info = self.common_ports.get(port, {
                    'service': f'UDP-{port}',
                    'description': f'Unknown UDP service on port {port}',
                    'risk': 'medium',
                    'banner': False,
                    'protocol': 'udp'
                })
                
                port_info.update({
                    'service': service_info['service'],
                    'description': service_info['description'],
                    'risk_level': service_info['risk']
                })
                
                # Add response data if available
                if data:
                    try:
                        response = data.decode('utf-8', errors='ignore')[:100]
                        port_info['response'] = response
                    except:
                        port_info['response'] = f"Binary data ({len(data)} bytes)"
                
                sock.close()
                return port_info
                
            except socket.timeout:
                # No response - could be open but not responding, or filtered
                # For UDP, we'll consider it as potentially open
                connect_time = time.time() - start_time
                
                port_info = {
                    'port': port,
                    'protocol': 'UDP',
                    'state': 'open|filtered',
                    'response_time': round(connect_time * 1000, 2),
                    'scanner': 'advanced_python'
                }
                
                service_info = self.common_ports.get(port, {
                    'service': f'UDP-{port}',
                    'description': f'Unknown UDP service on port {port}',
                    'risk': 'medium',
                    'protocol': 'udp'
                })
                
                port_info.update({
                    'service': service_info['service'],
                    'description': service_info['description'],
                    'risk_level': service_info['risk']
                })
                
                sock.close()
                return port_info
                
        except Exception as e:
            try:
                sock.close()
            except:
                pass
            return None
    
    def _get_udp_probe(self, port: int) -> bytes:
        """Get appropriate UDP probe for specific services"""
        if port == 53:  # DNS
            # DNS query for google.com
            return b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
        elif port == 161:  # SNMP
            # SNMP get request
            return b'\x30\x26\x02\x01\x00\x04\x06public\xa0\x19\x02\x04\x00\x00\x00\x00\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x05\x00'
        elif port == 123:  # NTP
            # NTP request
            return b'\x1b' + b'\x00' * 47
        elif port == 137:  # NetBIOS
            # NetBIOS name query
            return b'\x82\x28\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x20CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00\x21\x00\x01'
        elif port == 1900:  # UPnP
            # UPnP discovery
            return b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nST: upnp:rootdevice\r\nMX: 3\r\n\r\n'
        else:
            # Generic UDP probe
            return b'\x00\x00\x00\x00'
    
    def _grab_banner(self, sock: socket.socket, port: int) -> Optional[str]:
        """
        Attempt to grab service banner
        """
        try:
            sock.settimeout(self.banner_timeout)
            
            # Send appropriate probe based on port
            if port == 80 or port == 8080:
                # HTTP probe
                sock.send(b'GET / HTTP/1.1\r\nHost: target\r\n\r\n')
            elif port == 21:
                # FTP - just wait for banner
                pass
            elif port == 22:
                # SSH - just wait for banner
                pass
            elif port == 25:
                # SMTP - just wait for banner
                pass
            elif port == 110:
                # POP3 - just wait for banner
                pass
            elif port == 143:
                # IMAP - just wait for banner
                pass
            else:
                # Generic probe
                sock.send(b'\r\n')
            
            # Try to receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            return banner if banner else None
            
        except:
            return None
    
    def _identify_service_from_banner(self, banner: str) -> Optional[str]:
        """
        Identify service from banner text
        """
        banner_lower = banner.lower()
        
        for signature, service in self.service_signatures.items():
            if signature.lower() in banner_lower:
                return service
        
        return None
    
    def scan_ports_threaded(self, ip: str, ports: List[Tuple[int, str]] = None, max_workers: int = None) -> List[Dict]:
        """
        Scan multiple ports using threading for speed
        """
        if ports is None:
            # Use prioritized port list
            ports = self._get_prioritized_ports()
        
        if max_workers is None:
            max_workers = min(self.max_workers, len(ports))
        
        open_ports = []
        
        # Use ThreadPoolExecutor for concurrent scanning
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all port scan tasks
            future_to_port = {}
            for port_info in ports:
                if isinstance(port_info, tuple):
                    port, protocol = port_info
                else:
                    port, protocol = port_info, 'tcp'
                
                future = executor.submit(self.scan_port, ip, port, protocol)
                future_to_port[future] = (port, protocol)
            
            # Collect results with timeout
            try:
                for future in as_completed(future_to_port, timeout=45):
                    result = future.result()
                    if result:
                        open_ports.append(result)
            except Exception as e:
                logger.warning(f"Port scan timeout or error for {ip}: {e}")
                # Cancel remaining futures
                for future in future_to_port:
                    future.cancel()
        
        # Sort by risk level and port number
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        open_ports.sort(key=lambda x: (risk_order.get(x['risk_level'], 4), x['port']))
        
        return open_ports
    
    def _get_prioritized_ports(self) -> List[Tuple[int, str]]:
        """
        Get prioritized list of (port, protocol) tuples to scan
        Critical and high-risk ports first, then common ports
        """
        critical_ports = []
        high_ports = []
        medium_ports = []
        low_ports = []
        
        for port, info in self.common_ports.items():
            risk = info.get('risk', 'medium')
            protocol = info.get('protocol', 'tcp')
            port_tuple = (port, protocol)
            
            if risk == 'critical':
                critical_ports.append(port_tuple)
            elif risk == 'high':
                high_ports.append(port_tuple)
            elif risk == 'medium':
                medium_ports.append(port_tuple)
            else:
                low_ports.append(port_tuple)
        
        # Return prioritized list
        return critical_ports + high_ports + medium_ports + low_ports
    
    def quick_scan(self, ip: str) -> List[Dict]:
        """
        Quick scan of most critical ports
        """
        critical_ports = [(port, info.get('protocol', 'tcp')) 
                         for port, info in self.common_ports.items() 
                         if info.get('risk') in ['critical', 'high']]
        
        return self.scan_ports_threaded(ip, critical_ports, max_workers=20)
    
    def comprehensive_scan(self, ip: str) -> List[Dict]:
        """
        Comprehensive scan of all known ports
        """
        return self.scan_ports_threaded(ip, max_workers=30)
    
    def adaptive_scan(self, ip: str) -> List[Dict]:
        """
        Adaptive scanning strategy:
        1. Quick scan of critical ports
        2. If ports found, expand to comprehensive scan
        3. Smart timeout management
        """
        logger.info(f"Starting adaptive scan for {ip}")
        
        # Phase 1: Quick scan of critical ports
        critical_ports = self.quick_scan(ip)
        
        if not critical_ports:
            # No critical ports found, try medium-risk ports
            medium_ports = [(port, info.get('protocol', 'tcp')) 
                           for port, info in self.common_ports.items() 
                           if info.get('risk') == 'medium']
            medium_results = self.scan_ports_threaded(ip, medium_ports[:20], max_workers=15)
            return medium_results
        
        # Phase 2: Found some ports, do comprehensive scan
        logger.info(f"Found {len(critical_ports)} critical ports, expanding scan")
        all_ports = self.comprehensive_scan(ip)
        
        return all_ports
    
    def get_scanner_info(self) -> Dict:
        """Get scanner information"""
        return {
            'scanner_type': 'advanced_python',
            'requires_admin': False,
            'external_dependencies': False,
            'capabilities': {
                'service_detection': True,
                'banner_grabbing': True,
                'risk_assessment': True,
                'concurrent_scanning': True,
                'adaptive_scanning': True
            },
            'max_workers': self.max_workers,
            'timeout': self.scan_timeout
        }
    
    def scan_with_progress(self, ip: str, progress_callback=None) -> List[Dict]:
        """
        Scan with progress reporting
        """
        ports = self._get_prioritized_ports()
        total_ports = len(ports)
        completed = 0
        open_ports = []
        
        def scan_with_callback(port_info):
            nonlocal completed
            if isinstance(port_info, tuple):
                port, protocol = port_info
            else:
                port, protocol = port_info, 'tcp'
                
            result = self.scan_port(ip, port, protocol)
            completed += 1
            
            if progress_callback:
                progress = int((completed / total_ports) * 100)
                progress_callback(progress, completed, total_ports)
            
            return result
        
        # Scan with progress tracking
        with ThreadPoolExecutor(max_workers=min(30, total_ports)) as executor:
            future_to_port = {
                executor.submit(scan_with_callback, port_info): port_info 
                for port_info in ports
            }
            
            try:
                for future in as_completed(future_to_port, timeout=60):
                    result = future.result()
                    if result:
                        open_ports.append(result)
            except Exception as e:
                logger.warning(f"Progress scan timeout for {ip}: {e}")
                for future in future_to_port:
                    future.cancel()
        
        # Sort results
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        open_ports.sort(key=lambda x: (risk_order.get(x['risk_level'], 4), x['port']))
        
        return open_ports 