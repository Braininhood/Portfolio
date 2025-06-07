"""
Advanced Network Scan Engine
Professional-grade network scanning with comprehensive capabilities
"""

import asyncio
import ipaddress
import json
import logging
import socket
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import psutil
from django.utils import timezone
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@dataclass
class ScanTarget:
    """Represents a scan target with configuration"""
    ip: str
    ports: List[int] = None
    hostname: str = ""
    mac_address: str = ""
    exclude: bool = False


@dataclass
class PortResult:
    """Represents a port scan result"""
    port: int
    protocol: str
    state: str
    service: str = ""
    version: str = ""
    banner: str = ""
    risk_level: str = "medium"
    confidence: float = 0.0
    response_time: float = 0.0


@dataclass
class HostResult:
    """Represents a host scan result"""
    ip: str
    hostname: str = ""
    mac_address: str = ""
    os_info: str = ""
    status: str = "unknown"
    response_time: float = 0.0
    ports: List[PortResult] = None
    services: List[Dict] = None
    vulnerabilities: List[Dict] = None
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []
        if self.services is None:
            self.services = []
        if self.vulnerabilities is None:
            self.vulnerabilities = []


class ScanTechnique:
    """Base class for scan techniques"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    async def scan_port(self, ip: str, port: int, timeout: float = 1.0) -> Optional[PortResult]:
        """Scan a single port"""
        raise NotImplementedError
    
    async def scan_host(self, ip: str, ports: List[int], timeout: float = 1.0) -> List[PortResult]:
        """Scan multiple ports on a host"""
        tasks = [self.scan_port(ip, port, timeout) for port in ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, PortResult)]


class TCPConnectScan(ScanTechnique):
    """TCP Connect scan technique"""
    
    def __init__(self):
        super().__init__("TCP Connect", "Full TCP connection scan")
    
    async def scan_port(self, ip: str, port: int, timeout: float = 1.0) -> Optional[PortResult]:
        """Perform TCP connect scan on a port"""
        try:
            start_time = time.time()
            
            # Create socket and attempt connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((ip, port))
            response_time = (time.time() - start_time) * 1000
            
            sock.close()
            
            if result == 0:
                # Port is open, try to get service info
                service_info = await self._get_service_info(port)
                banner = await self._grab_banner(ip, port, timeout)
                
                return PortResult(
                    port=port,
                    protocol="TCP",
                    state="open",
                    service=service_info.get('service', 'unknown'),
                    banner=banner,
                    risk_level=service_info.get('risk_level', 'medium'),
                    confidence=0.9,
                    response_time=response_time
                )
        except Exception as e:
            logger.debug(f"TCP connect scan error for {ip}:{port} - {e}")
        
        return None
    
    async def _get_service_info(self, port: int) -> Dict:
        """Get service information for a port"""
        # Common service mappings
        services = {
            21: {'service': 'ftp', 'risk_level': 'high'},
            22: {'service': 'ssh', 'risk_level': 'medium'},
            23: {'service': 'telnet', 'risk_level': 'critical'},
            25: {'service': 'smtp', 'risk_level': 'medium'},
            53: {'service': 'dns', 'risk_level': 'low'},
            80: {'service': 'http', 'risk_level': 'medium'},
            110: {'service': 'pop3', 'risk_level': 'medium'},
            135: {'service': 'rpc', 'risk_level': 'high'},
            139: {'service': 'netbios', 'risk_level': 'high'},
            143: {'service': 'imap', 'risk_level': 'medium'},
            443: {'service': 'https', 'risk_level': 'low'},
            445: {'service': 'smb', 'risk_level': 'critical'},
            993: {'service': 'imaps', 'risk_level': 'low'},
            995: {'service': 'pop3s', 'risk_level': 'low'},
            1433: {'service': 'mssql', 'risk_level': 'critical'},
            3306: {'service': 'mysql', 'risk_level': 'critical'},
            3389: {'service': 'rdp', 'risk_level': 'high'},
            5432: {'service': 'postgresql', 'risk_level': 'critical'},
            8080: {'service': 'http-proxy', 'risk_level': 'medium'},
        }
        
        return services.get(port, {'service': 'unknown', 'risk_level': 'medium'})
    
    async def _grab_banner(self, ip: str, port: int, timeout: float = 2.0) -> str:
        """Attempt to grab service banner"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            # Send HTTP request for web services
            if port in [80, 8080, 8000, 8888]:
                sock.send(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
            elif port == 443:
                # For HTTPS, just try to read without sending
                pass
            elif port in [21, 22, 23, 25, 110, 143]:
                # These services usually send banner immediately
                pass
            else:
                # Send generic probe
                sock.send(b"\r\n")
            
            # Try to receive banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            sock.close()
            
            return banner[:200]  # Limit banner length
            
        except Exception:
            return ""


class TCPSynScan(ScanTechnique):
    """TCP SYN stealth scan technique"""
    
    def __init__(self):
        super().__init__("TCP SYN", "Stealth SYN scan (requires raw sockets)")
    
    async def scan_port(self, ip: str, port: int, timeout: float = 1.0) -> Optional[PortResult]:
        """Perform TCP SYN scan (fallback to connect scan if no raw socket access)"""
        # For now, fallback to connect scan since raw sockets require admin privileges
        tcp_scan = TCPConnectScan()
        result = await tcp_scan.scan_port(ip, port, timeout)
        if result:
            result.protocol = "TCP (SYN)"
        return result


class UDPScan(ScanTechnique):
    """UDP scan technique"""
    
    def __init__(self):
        super().__init__("UDP", "UDP port scan")
    
    async def scan_port(self, ip: str, port: int, timeout: float = 2.0) -> Optional[PortResult]:
        """Perform UDP scan on a port"""
        try:
            start_time = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            
            # Send UDP probe
            if port == 53:  # DNS
                probe = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01'
            elif port == 161:  # SNMP
                probe = b'\x30\x26\x02\x01\x01\x04\x06\x70\x75\x62\x6c\x69\x63\xa0\x19\x02\x04\x00\x00\x00\x00\x02\x01\x00\x02\x01\x00\x30\x0b\x30\x09\x06\x05\x2b\x06\x01\x02\x01\x05\x00'
            else:
                probe = b'\x00' * 4
            
            sock.sendto(probe, (ip, port))
            
            try:
                data, addr = sock.recvfrom(1024)
                response_time = (time.time() - start_time) * 1000
                
                service_info = await self._get_udp_service_info(port)
                
                return PortResult(
                    port=port,
                    protocol="UDP",
                    state="open",
                    service=service_info.get('service', 'unknown'),
                    risk_level=service_info.get('risk_level', 'medium'),
                    confidence=0.7,
                    response_time=response_time
                )
            except socket.timeout:
                # UDP timeout doesn't necessarily mean closed
                pass
            
            sock.close()
            
        except Exception as e:
            logger.debug(f"UDP scan error for {ip}:{port} - {e}")
        
        return None
    
    async def _get_udp_service_info(self, port: int) -> Dict:
        """Get UDP service information"""
        services = {
            53: {'service': 'dns', 'risk_level': 'low'},
            67: {'service': 'dhcp', 'risk_level': 'medium'},
            68: {'service': 'dhcp-client', 'risk_level': 'low'},
            69: {'service': 'tftp', 'risk_level': 'high'},
            123: {'service': 'ntp', 'risk_level': 'low'},
            161: {'service': 'snmp', 'risk_level': 'critical'},
            162: {'service': 'snmp-trap', 'risk_level': 'medium'},
            500: {'service': 'ipsec', 'risk_level': 'medium'},
            1194: {'service': 'openvpn', 'risk_level': 'medium'},
            1900: {'service': 'upnp', 'risk_level': 'high'},
        }
        
        return services.get(port, {'service': 'unknown', 'risk_level': 'medium'})


class ServiceDetector:
    """Advanced service detection and version identification"""
    
    def __init__(self):
        self.service_probes = self._load_service_probes()
    
    def _load_service_probes(self) -> Dict:
        """Load service detection probes"""
        return {
            'http': {
                'probe': b'GET / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: NetworkScanner/1.0\r\n\r\n',
                'ports': [80, 8080, 8000, 8888, 8443],
                'signatures': [
                    (b'Server:', 'server_header'),
                    (b'Apache', 'apache'),
                    (b'nginx', 'nginx'),
                    (b'IIS', 'iis'),
                    (b'lighttpd', 'lighttpd'),
                ]
            },
            'ssh': {
                'probe': b'',
                'ports': [22],
                'signatures': [
                    (b'SSH-', 'ssh_version'),
                    (b'OpenSSH', 'openssh'),
                    (b'libssh', 'libssh'),
                ]
            },
            'ftp': {
                'probe': b'',
                'ports': [21],
                'signatures': [
                    (b'220', 'ftp_banner'),
                    (b'vsftpd', 'vsftpd'),
                    (b'ProFTPD', 'proftpd'),
                    (b'FileZilla', 'filezilla'),
                ]
            },
            'smtp': {
                'probe': b'EHLO scanner.local\r\n',
                'ports': [25, 587],
                'signatures': [
                    (b'220', 'smtp_banner'),
                    (b'Postfix', 'postfix'),
                    (b'Sendmail', 'sendmail'),
                    (b'Exim', 'exim'),
                ]
            }
        }
    
    async def detect_service(self, ip: str, port: int, timeout: float = 3.0) -> Dict:
        """Detect service and version on a port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            
            # Try to identify service based on port and response
            service_info = {'service': 'unknown', 'version': '', 'details': {}}
            
            for service_name, probe_info in self.service_probes.items():
                if port in probe_info['ports']:
                    # Send probe
                    if probe_info['probe']:
                        probe = probe_info['probe'].replace(b'{host}', ip.encode())
                        sock.send(probe)
                    
                    # Read response
                    try:
                        response = sock.recv(2048)
                        
                        # Check signatures
                        for signature, sig_type in probe_info['signatures']:
                            if signature in response:
                                service_info['service'] = service_name
                                service_info['details'][sig_type] = True
                                
                                # Extract version if possible
                                if sig_type == 'ssh_version':
                                    version = self._extract_ssh_version(response)
                                    if version:
                                        service_info['version'] = version
                                elif sig_type == 'server_header':
                                    version = self._extract_http_server(response)
                                    if version:
                                        service_info['version'] = version
                        
                        break
                    except socket.timeout:
                        continue
            
            sock.close()
            return service_info
            
        except Exception as e:
            logger.debug(f"Service detection error for {ip}:{port} - {e}")
            return {'service': 'unknown', 'version': '', 'details': {}}
    
    def _extract_ssh_version(self, response: bytes) -> str:
        """Extract SSH version from banner"""
        try:
            banner = response.decode('utf-8', errors='ignore')
            if 'SSH-' in banner:
                version_line = banner.split('\n')[0]
                return version_line.strip()
        except:
            pass
        return ""
    
    def _extract_http_server(self, response: bytes) -> str:
        """Extract HTTP server version from headers"""
        try:
            headers = response.decode('utf-8', errors='ignore')
            for line in headers.split('\n'):
                if line.lower().startswith('server:'):
                    return line.split(':', 1)[1].strip()
        except:
            pass
        return ""


class OSDetector:
    """Operating system detection and fingerprinting"""
    
    def __init__(self):
        self.os_signatures = self._load_os_signatures()
    
    def _load_os_signatures(self) -> Dict:
        """Load OS detection signatures"""
        return {
            'windows': {
                'tcp_window_size': [8192, 65535],
                'ttl_range': [128, 128],
                'services': ['135', '139', '445', '3389'],
                'signatures': ['Microsoft', 'Windows', 'IIS']
            },
            'linux': {
                'tcp_window_size': [5840, 65535],
                'ttl_range': [64, 64],
                'services': ['22', '80', '443'],
                'signatures': ['Apache', 'nginx', 'OpenSSH']
            },
            'macos': {
                'tcp_window_size': [65535, 65535],
                'ttl_range': [64, 64],
                'services': ['22', '548', '631'],
                'signatures': ['Darwin', 'Mac OS']
            }
        }
    
    async def detect_os(self, host_result: HostResult) -> str:
        """Detect operating system based on various indicators"""
        scores = {}
        
        for os_name, signatures in self.os_signatures.items():
            score = 0
            
            # Check open ports
            open_ports = [str(p.port) for p in host_result.ports if p.state == 'open']
            common_ports = set(signatures['services']) & set(open_ports)
            score += len(common_ports) * 10
            
            # Check service banners
            for port_result in host_result.ports:
                for sig in signatures['signatures']:
                    if sig.lower() in port_result.banner.lower():
                        score += 20
            
            scores[os_name] = score
        
        # Return OS with highest score
        if scores:
            best_os = max(scores, key=scores.get)
            if scores[best_os] > 0:
                return best_os
        
        return "unknown"


class VulnerabilityScanner:
    """Basic vulnerability detection"""
    
    def __init__(self):
        self.vulnerability_checks = self._load_vulnerability_checks()
    
    def _load_vulnerability_checks(self) -> List[Dict]:
        """Load vulnerability check definitions"""
        return [
            {
                'id': 'WEAK_SSH',
                'name': 'Weak SSH Configuration',
                'description': 'SSH service may have weak configuration',
                'severity': 'medium',
                'check': self._check_weak_ssh
            },
            {
                'id': 'OPEN_TELNET',
                'name': 'Telnet Service Detected',
                'description': 'Insecure Telnet service is running',
                'severity': 'critical',
                'check': self._check_telnet
            },
            {
                'id': 'OPEN_FTP',
                'name': 'FTP Service Detected',
                'description': 'FTP service may allow anonymous access',
                'severity': 'high',
                'check': self._check_ftp
            },
            {
                'id': 'OPEN_SMB',
                'name': 'SMB Service Detected',
                'description': 'SMB service may be vulnerable to attacks',
                'severity': 'critical',
                'check': self._check_smb
            },
            {
                'id': 'WEAK_HTTP',
                'name': 'HTTP Service Without HTTPS',
                'description': 'Web service not using encryption',
                'severity': 'medium',
                'check': self._check_http_security
            }
        ]
    
    async def scan_vulnerabilities(self, host_result: HostResult) -> List[Dict]:
        """Scan for vulnerabilities on a host"""
        vulnerabilities = []
        
        for vuln_check in self.vulnerability_checks:
            try:
                if await vuln_check['check'](host_result):
                    vulnerabilities.append({
                        'id': vuln_check['id'],
                        'name': vuln_check['name'],
                        'description': vuln_check['description'],
                        'severity': vuln_check['severity'],
                        'discovered_at': timezone.now().isoformat()
                    })
            except Exception as e:
                logger.debug(f"Vulnerability check {vuln_check['id']} failed: {e}")
        
        return vulnerabilities
    
    async def _check_weak_ssh(self, host_result: HostResult) -> bool:
        """Check for weak SSH configuration"""
        ssh_ports = [p for p in host_result.ports if p.port == 22 and p.state == 'open']
        return len(ssh_ports) > 0
    
    async def _check_telnet(self, host_result: HostResult) -> bool:
        """Check for Telnet service"""
        telnet_ports = [p for p in host_result.ports if p.port == 23 and p.state == 'open']
        return len(telnet_ports) > 0
    
    async def _check_ftp(self, host_result: HostResult) -> bool:
        """Check for FTP service"""
        ftp_ports = [p for p in host_result.ports if p.port == 21 and p.state == 'open']
        return len(ftp_ports) > 0
    
    async def _check_smb(self, host_result: HostResult) -> bool:
        """Check for SMB service"""
        smb_ports = [p for p in host_result.ports if p.port in [139, 445] and p.state == 'open']
        return len(smb_ports) > 0
    
    async def _check_http_security(self, host_result: HostResult) -> bool:
        """Check for HTTP without HTTPS"""
        http_ports = [p for p in host_result.ports if p.port in [80, 8080] and p.state == 'open']
        https_ports = [p for p in host_result.ports if p.port in [443, 8443] and p.state == 'open']
        return len(http_ports) > 0 and len(https_ports) == 0


class AdvancedScanEngine:
    """Professional network scan engine with comprehensive capabilities"""
    
    def __init__(self):
        self.techniques = {
            'tcp_connect': TCPConnectScan(),
            'tcp_syn': TCPSynScan(),
            'udp': UDPScan(),
        }
        self.service_detector = ServiceDetector()
        self.os_detector = OSDetector()
        self.vulnerability_scanner = VulnerabilityScanner()
        self.executor = ThreadPoolExecutor(max_workers=100)
        
        # Performance monitoring
        self.start_time = None
        self.current_target = None
        self.current_risk_score = 0
        
        # Progress tracking optimization
        self.last_progress_update = 0
        self.update_threshold = 10  # Only update every 10%
        self.last_meaningful_update = 0
        self.meaningful_update_interval = 15  # Minimum 15 seconds between meaningful updates
        self.scan_stats = {
            'hosts_scanned': 0,
            'hosts_up': 0,
            'ports_scanned': 0,
            'open_ports_found': 0,
            'services_detected': 0,
            'vulnerabilities_found': 0,
            'scan_rate': 0.0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0
        }
        
        # Progress tracking optimization
        self.last_progress_update = 0
        self.update_threshold = 10  # Only update every 10%
        self.last_meaningful_update = 0
        self.meaningful_update_interval = 15  # Minimum 15 seconds between meaningful updates
    
    async def execute_scan(self, scan_config: Dict) -> Dict:
        """Execute a comprehensive network scan"""
        self.start_time = time.time()
        scan_id = scan_config.get('scan_id', str(uuid.uuid4()))
        
        logger.info(f"Starting advanced scan {scan_id}: {scan_config.get('scan_type', 'unknown')}")
        
        try:
            # Send scan started notification
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            if channel_layer:
                await channel_layer.group_send('network_monitor', {
                    'type': 'scan_started',
                    'scan_id': scan_id,
                    'scan_type': scan_config.get('scan_type'),
                    'target_range': scan_config.get('target_range'),
                    'timestamp': timezone.now().isoformat()
                })
            
            # Update scan status to running
            await self._update_scan_status(scan_id, 'running', 0, 'Initializing scan...', force_update=True)
            
            # Parse targets
            targets = await self._parse_targets(scan_config)
            total_targets = len(targets)
            
            if total_targets == 0:
                raise ValueError("No valid targets found")
            
            # Execute scan based on type
            scan_type = scan_config.get('scan_type', 'discovery')
            
            if scan_type == 'ping_sweep':
                results = await self._execute_ping_sweep(scan_id, targets, scan_config)
            elif scan_type == 'port_scan':
                results = await self._execute_port_scan(scan_id, targets, scan_config)
            elif scan_type == 'service_detection':
                results = await self._execute_service_detection(scan_id, targets, scan_config)
            elif scan_type == 'os_fingerprinting':
                results = await self._execute_os_fingerprinting(scan_id, targets, scan_config)
            elif scan_type == 'vulnerability_scan':
                results = await self._execute_vulnerability_scan(scan_id, targets, scan_config)
            elif scan_type == 'comprehensive':
                results = await self._execute_comprehensive_scan(scan_id, targets, scan_config)
            elif scan_type == 'stealth_scan':
                results = await self._execute_stealth_scan(scan_id, targets, scan_config)
            else:
                results = await self._execute_discovery_scan(scan_id, targets, scan_config)
            
            # Calculate final statistics
            duration = time.time() - self.start_time
            self.scan_stats['scan_rate'] = self.scan_stats['hosts_scanned'] / duration if duration > 0 else 0
            
            # Store detailed scan results
            await self._store_scan_results(scan_id, results, scan_config)
            
            # Send scan completed notification
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            if channel_layer:
                # Calculate final stats for notification
                hosts_scanned = len(results)
                hosts_up = len([r for r in results if r.status == 'up'])
                open_ports = sum(len([p for p in r.ports if p.state == 'open']) for r in results)
                services = sum(len(r.services) for r in results)
                vulnerabilities = sum(len(r.vulnerabilities) for r in results)
                risk_score = self._calculate_risk_score(results)
                
                await channel_layer.group_send('network_monitor', {
                    'type': 'scan_completed',
                    'scan_id': scan_id,
                    'status': 'completed',
                    'duration': duration,
                    'hosts_scanned': hosts_scanned,
                    'hosts_up': hosts_up,
                    'open_ports_found': open_ports,
                    'services_detected': services,
                    'vulnerabilities_found': vulnerabilities,
                    'risk_score': risk_score,
                    'timestamp': timezone.now().isoformat()
                })
            
            # Finalize scan
            await self._update_scan_status(scan_id, 'completed', 100, 'Scan completed successfully', force_update=True)
            
            return {
                'scan_id': scan_id,
                'status': 'completed',
                'results': results,
                'statistics': self.scan_stats,
                'duration': duration
            }
            
        except Exception as e:
            logger.error(f"Scan {scan_id} failed: {e}")
            
            # Send scan failed notification
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            if channel_layer:
                await channel_layer.group_send('network_monitor', {
                    'type': 'scan_failed',
                    'scan_id': scan_id,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                })
            
            await self._update_scan_status(scan_id, 'failed', 0, f'Scan failed: {str(e)}', force_update=True)
            raise
    
    async def _parse_targets(self, scan_config: Dict) -> List[ScanTarget]:
        """Parse target specification into individual targets"""
        target_range = scan_config.get('target_range', '')
        exclude_hosts = scan_config.get('exclude_hosts', '').split(',')
        exclude_hosts = [h.strip() for h in exclude_hosts if h.strip()]
        
        targets = []
        
        try:
            # Handle CIDR notation
            if '/' in target_range:
                network = ipaddress.IPv4Network(target_range, strict=False)
                for ip in network.hosts():
                    ip_str = str(ip)
                    if ip_str not in exclude_hosts:
                        targets.append(ScanTarget(ip=ip_str))
            
            # Handle range notation (e.g., 192.168.1.1-50 or 192.168.1.1-192.168.1.10)
            elif '-' in target_range and '.' in target_range:
                if target_range.count('.') >= 6:  # Full IP range format: 192.168.1.1-192.168.1.10
                    start_ip, end_ip = target_range.split('-', 1)
                    start_ip = start_ip.strip()
                    end_ip = end_ip.strip()
                    
                    # Parse start and end IPs
                    start_parts = start_ip.split('.')
                    end_parts = end_ip.split('.')
                    
                    if len(start_parts) == 4 and len(end_parts) == 4:
                        # Ensure same network range (first 3 octets)
                        if start_parts[:3] == end_parts[:3]:
                            start_host = int(start_parts[3])
                            end_host = int(end_parts[3])
                            
                            base_ip = '.'.join(start_parts[:3])
                            for i in range(start_host, end_host + 1):
                                ip_str = f"{base_ip}.{i}"
                                if ip_str not in exclude_hosts:
                                    targets.append(ScanTarget(ip=ip_str))
                        else:
                            raise ValueError(f"IP range spans different subnets: {target_range}")
                    else:
                        raise ValueError(f"Invalid IP format in range: {target_range}")
                else:  # Short format: 192.168.1.1-10
                    base_ip, range_part = target_range.rsplit('.', 1)
                    if '-' in range_part:
                        start, end = range_part.split('-')
                        for i in range(int(start), int(end) + 1):
                            ip_str = f"{base_ip}.{i}"
                            if ip_str not in exclude_hosts:
                                targets.append(ScanTarget(ip=ip_str))
            
            # Handle comma-separated IPs
            elif ',' in target_range:
                ips = [ip.strip() for ip in target_range.split(',')]
                for ip in ips:
                    if ip and ip not in exclude_hosts:
                        targets.append(ScanTarget(ip=ip))
            
            # Single IP
            else:
                if target_range and target_range not in exclude_hosts:
                    targets.append(ScanTarget(ip=target_range))
        
        except Exception as e:
            logger.error(f"Error parsing targets: {e}")
            raise ValueError(f"Invalid target specification: {target_range}")
        
        return targets
    
    async def _execute_ping_sweep(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute ping sweep scan"""
        results = []
        total_targets = len(targets)
        
        # Ping all targets
        for i, target in enumerate(targets):
            progress = int((i / total_targets) * 100)
            await self._update_scan_status(scan_id, 'running', progress, f'Pinging {target.ip}')
            
            is_alive, response_time = await self._ping_host(target.ip)
            
            if is_alive:
                host_result = HostResult(
                    ip=target.ip,
                    status='up',
                    response_time=response_time
                )
                results.append(host_result)
                self.scan_stats['hosts_scanned'] += 1
                self.scan_stats['hosts_up'] = self.scan_stats.get('hosts_up', 0) + 1
        
        return results
    
    async def _execute_port_scan(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute port scan"""
        results = []
        total_targets = len(targets)
        
        # Parse port specification
        ports = self._parse_ports(config.get('target_ports', '1-1000'))
        techniques = config.get('scan_techniques', ['tcp_connect'])
        
        for i, target in enumerate(targets):
            progress = int((i / total_targets) * 100)
            self.current_target = target.ip
            await self._update_scan_status(scan_id, 'running', progress, f'Scanning ports on {target.ip}')
            
            # First check if host is alive
            is_alive, response_time = await self._ping_host(target.ip)
            
            if is_alive:
                host_result = HostResult(
                    ip=target.ip,
                    status='up',
                    response_time=response_time
                )
                
                # Scan ports using specified techniques
                for technique_name in techniques:
                    if technique_name in self.techniques:
                        technique = self.techniques[technique_name]
                        port_results = await technique.scan_host(target.ip, ports, timeout=2.0)
                        host_result.ports.extend(port_results)
                        self.scan_stats['ports_scanned'] += len(ports)
                
                # Always include alive hosts, even if no open ports found
                results.append(host_result)
                self.scan_stats['hosts_scanned'] += 1
                self.scan_stats['hosts_up'] = self.scan_stats.get('hosts_up', 0) + 1
                
                # Update port statistics
                if host_result.ports:
                    open_ports = [p for p in host_result.ports if p.state == 'open']
                    self.scan_stats['open_ports_found'] = self.scan_stats.get('open_ports_found', 0) + len(open_ports)
        
        return results
    
    async def _execute_service_detection(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute service detection scan"""
        # First do port scan
        port_results = await self._execute_port_scan(scan_id, targets, config)
        
        # Then detect services on open ports
        total_hosts = len(port_results)
        
        for i, host_result in enumerate(port_results):
            progress = int((i / total_hosts) * 100)
            await self._update_scan_status(scan_id, 'running', progress, f'Detecting services on {host_result.ip}')
            
            for port_result in host_result.ports:
                if port_result.state == 'open':
                    service_info = await self.service_detector.detect_service(
                        host_result.ip, port_result.port
                    )
                    
                    port_result.service = service_info.get('service', port_result.service)
                    port_result.version = service_info.get('version', '')
                    
                    # Add to services list
                    host_result.services.append({
                        'port': port_result.port,
                        'service': port_result.service,
                        'version': port_result.version,
                        'details': service_info.get('details', {})
                    })
        
        return port_results
    
    async def _execute_os_fingerprinting(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute OS fingerprinting scan"""
        # First do service detection
        service_results = await self._execute_service_detection(scan_id, targets, config)
        
        # Then detect OS
        total_hosts = len(service_results)
        
        for i, host_result in enumerate(service_results):
            progress = int((i / total_hosts) * 100)
            await self._update_scan_status(scan_id, 'running', progress, f'Fingerprinting OS on {host_result.ip}')
            
            os_info = await self.os_detector.detect_os(host_result)
            host_result.os_info = os_info
        
        return service_results
    
    async def _execute_vulnerability_scan(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute vulnerability scan"""
        # First do OS fingerprinting
        os_results = await self._execute_os_fingerprinting(scan_id, targets, config)
        
        # Then scan for vulnerabilities
        total_hosts = len(os_results)
        
        for i, host_result in enumerate(os_results):
            progress = int((i / total_hosts) * 100)
            await self._update_scan_status(scan_id, 'running', progress, f'Scanning vulnerabilities on {host_result.ip}')
            
            vulnerabilities = await self.vulnerability_scanner.scan_vulnerabilities(host_result)
            host_result.vulnerabilities = vulnerabilities
        
        return os_results
    
    async def _execute_comprehensive_scan(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute comprehensive scan with all techniques"""
        return await self._execute_vulnerability_scan(scan_id, targets, config)
    
    async def _execute_stealth_scan(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute stealth scan using SYN scan technique"""
        results = []
        total_targets = len(targets)
        
        # Parse port specification - stealth scans typically focus on key ports
        ports = self._parse_ports(config.get('target_ports', '22,80,443,135,139,445,3389'))
        
        for i, target in enumerate(targets):
            progress = int((i / total_targets) * 100)
            await self._update_scan_status(scan_id, 'running', progress, f'Stealth scanning {target.ip}')
            
            # First check if host is alive using stealth technique
            is_alive, response_time = await self._ping_host(target.ip)
            
            if is_alive:
                host_result = HostResult(
                    ip=target.ip,
                    status='up',
                    response_time=response_time
                )
                
                # Use TCP SYN scan for stealth
                if 'tcp_syn' in self.techniques:
                    technique = self.techniques['tcp_syn']
                    port_results = await technique.scan_host(target.ip, ports, timeout=3.0)
                    host_result.ports.extend(port_results)
                    self.scan_stats['ports_scanned'] += len(ports)
                else:
                    # Fallback to connect scan but with slower timing
                    technique = self.techniques['tcp_connect']
                    port_results = await technique.scan_host(target.ip, ports, timeout=5.0)
                    host_result.ports.extend(port_results)
                    self.scan_stats['ports_scanned'] += len(ports)
                
                # Always include alive hosts for comprehensive results
                results.append(host_result)
                self.scan_stats['hosts_scanned'] += 1
                self.scan_stats['hosts_up'] = self.scan_stats.get('hosts_up', 0) + 1
                
                # Update port statistics
                if host_result.ports:
                    open_ports = [p for p in host_result.ports if p.state == 'open']
                    self.scan_stats['open_ports_found'] = self.scan_stats.get('open_ports_found', 0) + len(open_ports)
                
                # Add delay for stealth
                await asyncio.sleep(0.5)
        
        return results
    
    async def _execute_discovery_scan(self, scan_id: str, targets: List[ScanTarget], config: Dict) -> List[HostResult]:
        """Execute basic discovery scan"""
        return await self._execute_ping_sweep(scan_id, targets, config)
    
    async def _ping_host(self, ip: str, timeout: float = 2.0) -> Tuple[bool, float]:
        """Enhanced host discovery - try multiple methods to detect alive hosts"""
        try:
            start_time = time.time()
            
            # Method 1: Try common ports with short timeout
            common_ports = [80, 443, 22, 21, 23, 25, 53, 135, 139, 445, 3389, 8080]
            
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)  # Very short timeout for port testing
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if result == 0:
                        response_time = (time.time() - start_time) * 1000
                        return True, response_time
                        
                except Exception:
                    continue
            
            # Method 2: Try UDP ping to common services
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1.0)
                # Try DNS query
                sock.sendto(b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01', (ip, 53))
                sock.recv(512)  # Try to receive response
                sock.close()
                response_time = (time.time() - start_time) * 1000
                return True, response_time
            except Exception:
                pass
            
            # Method 3: ARP table check for local network hosts
            if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                try:
                    import subprocess
                    import platform
                    
                    if platform.system().lower() == "windows":
                        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=2)
                        if ip in result.stdout:
                            response_time = (time.time() - start_time) * 1000
                            return True, response_time
                    else:
                        result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=2)
                        if ip in result.stdout:
                            response_time = (time.time() - start_time) * 1000
                            return True, response_time
                except Exception:
                    pass
            
            return False, 0.0
            
        except Exception:
            return False, 0.0
    
    def _parse_ports(self, port_spec: str) -> List[int]:
        """Parse port specification into list of ports"""
        ports = []
        
        if not port_spec:
            # Default common ports
            return [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 3306, 3389, 5432, 8080]
        
        for part in port_spec.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                try:
                    start_port = int(start.strip())
                    end_port = int(end.strip())
                    ports.extend(range(start_port, end_port + 1))
                except ValueError:
                    continue
            else:
                try:
                    ports.append(int(part))
                except ValueError:
                    continue
        
        return sorted(list(set(ports)))  # Remove duplicates and sort
    
    async def _update_scan_status(self, scan_id: str, status: str, progress: int, message: str, force_update: bool = False):
        """Update scan status in database with optimized progress updates"""
        try:
            from .models import NetworkScan
            current_time = time.time()
            
            # Check if we should send this update to reduce false-positives
            should_update = (
                force_update or  # Force update (e.g., start/complete/error)
                status in ['running', 'completed', 'failed'] or  # Important status changes
                abs(progress - self.last_progress_update) >= self.update_threshold or  # Significant progress
                (current_time - self.last_meaningful_update) >= self.meaningful_update_interval  # Time threshold
            )
            
            if not should_update:
                return  # Skip this update to reduce noise
            
            # Update tracking variables
            self.last_progress_update = progress
            if should_update and status == 'running':
                self.last_meaningful_update = current_time
            
            @database_sync_to_async
            def update_scan():
                try:
                    scan = NetworkScan.objects.get(scan_id=scan_id)
                    scan.status = status
                    scan.progress_percentage = progress
                    scan.current_phase = message
                    
                    if status == 'completed':
                        scan.completed_at = timezone.now()
                        scan.hosts_up = self.scan_stats.get('hosts_scanned', 0)
                        scan.total_ports_scanned = self.scan_stats.get('ports_scanned', 0)
                        scan.scan_rate = self.scan_stats.get('scan_rate', 0)
                    elif status == 'failed':
                        scan.completed_at = timezone.now()
                        scan.add_error(message)
                    
                    scan.save()
                    return scan
                except NetworkScan.DoesNotExist:
                    logger.error(f"Scan {scan_id} not found in database. Creating scan entry...")
                    # Try to create the scan if it doesn't exist
                    try:
                        scan = NetworkScan.objects.create(
                            scan_id=scan_id,
                            name=f"Auto-created scan {scan_id[:8]}",
                            scan_type='discovery',
                            target_range='192.168.1.0/24',
                            status=status,
                            progress_percentage=progress,
                            current_phase=message
                        )
                        logger.info(f"Created missing scan entry for {scan_id}")
                        return scan
                    except Exception as e:
                        logger.error(f"Failed to create scan entry for {scan_id}: {e}")
                        return None
            
            await update_scan()
            
            # Broadcast progress via WebSocket (only for meaningful updates)
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            
            if channel_layer:
                # Get current scan statistics
                hosts_scanned = self.scan_stats.get('hosts_scanned', 0)
                hosts_up = self.scan_stats.get('hosts_up', 0)
                open_ports = self.scan_stats.get('open_ports_found', 0)
                services = self.scan_stats.get('services_detected', 0)
                vulnerabilities = self.scan_stats.get('vulnerabilities_found', 0)
                
                await channel_layer.group_send('network_monitor', {
                    'type': 'scan_progress_update',
                    'scan_id': scan_id,
                    'status': status,
                    'progress_percentage': progress,
                    'current_phase': message,
                    'current_target': self.current_target,
                    'hosts_scanned': hosts_scanned,
                    'hosts_up': hosts_up,
                    'open_ports_found': open_ports,
                    'services_detected': services,
                    'vulnerabilities_found': vulnerabilities,
                    'risk_score': getattr(self, 'current_risk_score', 0),
                    'timestamp': timezone.now().isoformat(),
                    'update_type': 'meaningful' if force_update or status != 'running' else 'progress'
                })
        
        except Exception as e:
            logger.error(f"Error updating scan status: {e}")

    async def _store_scan_results(self, scan_id: str, results: List[HostResult], config: Dict):
        """Store comprehensive scan results in database"""
        try:
            from .models import NetworkScan
            
            # Calculate detailed statistics
            total_hosts_scanned = len(results)
            hosts_up = len([r for r in results if r.status == 'up'])
            total_open_ports = sum(len([p for p in r.ports if p.state == 'open']) for r in results)
            services_detected = sum(len(r.services) for r in results)
            vulnerabilities_found = sum(len(r.vulnerabilities) for r in results)
            
            logger.info(f"Storing scan results for {scan_id}: {total_hosts_scanned} hosts, {hosts_up} up, {total_open_ports} open ports, {services_detected} services, {vulnerabilities_found} vulns")
            
            # Calculate risk score based on findings
            risk_score = self._calculate_risk_score(results)
            
            # Convert results to JSON-serializable format
            host_results_json = []
            port_results_json = []
            service_results_json = []
            vulnerability_results_json = []
            
            for host_result in results:
                # Host result
                host_data = {
                    'ip': host_result.ip,
                    'hostname': host_result.hostname,
                    'mac_address': host_result.mac_address,
                    'os_info': host_result.os_info,
                    'status': host_result.status,
                    'response_time': host_result.response_time,
                    'ports_found': len([p for p in host_result.ports if p.state == 'open']),
                    'services_found': len(host_result.services),
                    'vulnerabilities_found': len(host_result.vulnerabilities)
                }
                host_results_json.append(host_data)
                logger.debug(f"Host {host_result.ip}: {host_data['ports_found']} ports, {host_data['services_found']} services")
                
                # Port results
                for port_result in host_result.ports:
                    if port_result.state == 'open':
                        port_data = {
                            'ip': host_result.ip,
                            'port': port_result.port,
                            'protocol': port_result.protocol,
                            'state': port_result.state,
                            'service': port_result.service,
                            'version': port_result.version,
                            'banner': port_result.banner,
                            'risk_level': port_result.risk_level,
                            'confidence': port_result.confidence,
                            'response_time': port_result.response_time
                        }
                        port_results_json.append(port_data)
                
                # Service results
                for service in host_result.services:
                    service_data = {
                        'ip': host_result.ip,
                        'port': service.get('port'),
                        'service': service.get('service'),
                        'version': service.get('version'),
                        'details': service.get('details', {})
                    }
                    service_results_json.append(service_data)
                
                # Vulnerability results
                for vuln in host_result.vulnerabilities:
                    vuln_data = {
                        'ip': host_result.ip,
                        'vulnerability': vuln.get('name'),
                        'severity': vuln.get('severity'),
                        'description': vuln.get('description'),
                        'cve': vuln.get('cve'),
                        'solution': vuln.get('solution')
                    }
                    vulnerability_results_json.append(vuln_data)
            
            logger.info(f"Converted to JSON: {len(host_results_json)} hosts, {len(port_results_json)} ports, {len(service_results_json)} services, {len(vulnerability_results_json)} vulns")
            
            @database_sync_to_async
            def store_results():
                try:
                    scan = NetworkScan.objects.get(scan_id=scan_id)
                    
                    # Update scan statistics
                    scan.total_hosts_scanned = total_hosts_scanned
                    scan.hosts_up = hosts_up
                    scan.hosts_down = total_hosts_scanned - hosts_up
                    scan.total_ports_scanned = self.scan_stats.get('ports_scanned', 0)
                    scan.open_ports_found = total_open_ports
                    scan.services_detected = services_detected
                    scan.vulnerabilities_found = vulnerabilities_found
                    
                    # Store detailed results
                    scan.host_results = host_results_json
                    scan.port_results = port_results_json
                    scan.service_results = service_results_json
                    scan.vulnerability_results = vulnerability_results_json
                    
                    # Store comprehensive scan results
                    scan.scan_results = {
                        'scan_type': config.get('scan_type'),
                        'target_range': config.get('target_range'),
                        'duration': time.time() - self.start_time,
                        'statistics': self.scan_stats,
                        'summary': {
                            'total_hosts': total_hosts_scanned,
                            'hosts_up': hosts_up,
                            'hosts_down': total_hosts_scanned - hosts_up,
                            'success_rate': (hosts_up / total_hosts_scanned * 100) if total_hosts_scanned > 0 else 0,
                            'open_ports': total_open_ports,
                            'services': services_detected,
                            'vulnerabilities': vulnerabilities_found,
                            'risk_score': risk_score
                        },
                        'performance': {
                            'scan_rate': self.scan_stats.get('scan_rate', 0),
                            'bandwidth_used': self.scan_stats.get('bandwidth_used', 0),
                            'cpu_usage_avg': self.scan_stats.get('cpu_usage_avg', 0),
                            'memory_usage_peak': self.scan_stats.get('memory_usage_peak', 0)
                        }
                    }
                    
                    # Update performance metrics
                    scan.scan_rate = self.scan_stats.get('scan_rate', 0)
                    scan.bandwidth_used = self.scan_stats.get('bandwidth_used', 0)
                    scan.cpu_usage_avg = self.scan_stats.get('cpu_usage_avg', 0)
                    scan.memory_usage_peak = self.scan_stats.get('memory_usage_peak', 0)
                    
                    scan.save()
                    
                    logger.info(f"Successfully stored scan results for {scan_id}: {scan.total_hosts_scanned} hosts, {scan.open_ports_found} ports, {scan.services_detected} services, risk score: {scan.risk_score}")
                    return scan
                    
                except NetworkScan.DoesNotExist:
                    logger.error(f"Scan {scan_id} not found when storing results")
                    return None
                except Exception as e:
                    logger.error(f"Database error storing scan results: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
            
            await store_results()
            
        except Exception as e:
            logger.error(f"Error storing scan results: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _calculate_risk_score(self, results: List[HostResult]) -> int:
        """Calculate overall risk score based on scan results"""
        risk_score = 0
        
        for host_result in results:
            # Base score for active host
            if host_result.status == 'up':
                risk_score += 5
            
            # Score for open ports
            open_ports = [p for p in host_result.ports if p.state == 'open']
            risk_score += len(open_ports) * 2
            
            # Higher score for risky services
            risky_ports = [22, 23, 135, 139, 445, 1433, 3306, 3389]
            for port_result in open_ports:
                if port_result.port in risky_ports:
                    risk_score += 5
                if port_result.service in ['telnet', 'ftp', 'smb', 'rdp']:
                    risk_score += 10
            
            # Score for vulnerabilities
            for vuln in host_result.vulnerabilities:
                severity = vuln.get('severity', 'medium').lower()
                if severity == 'critical':
                    risk_score += 25
                elif severity == 'high':
                    risk_score += 15
                elif severity == 'medium':
                    risk_score += 10
                elif severity == 'low':
                    risk_score += 5
        
        # Cap at 100
        return min(risk_score, 100)


# Global scan engine instance
scan_engine = AdvancedScanEngine() 