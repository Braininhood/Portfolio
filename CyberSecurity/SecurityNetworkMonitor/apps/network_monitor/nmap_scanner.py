#!/usr/bin/env python
"""
Nmap-based Port Scanner
Professional port scanning using Nmap for accurate and comprehensive results
"""
import subprocess
import json
import xml.etree.ElementTree as ET
import logging
import tempfile
import os
from typing import List, Dict, Optional
import socket

logger = logging.getLogger(__name__)

class NmapPortScanner:
    """Professional port scanner using Nmap"""
    
    def __init__(self):
        self.nmap_available = self._check_nmap_availability()
        
    def _check_nmap_availability(self) -> bool:
        """Check if Nmap is available on the system"""
        try:
            result = subprocess.run(['nmap', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Nmap is available for professional port scanning")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        logger.warning("Nmap not available, falling back to basic socket scanning")
        return False
    
    def scan_ports_nmap(self, ip: str, ports: List[int] = None, scan_type: str = "fast") -> List[Dict]:
        """
        Scan ports using Nmap for professional results
        
        Args:
            ip: Target IP address
            ports: List of ports to scan (None for default)
            scan_type: "fast", "comprehensive", or "stealth"
        """
        if not self.nmap_available:
            return self._fallback_socket_scan(ip, ports)
        
        try:
            # Build Nmap command
            cmd = ['nmap']
            
            # Scan type configuration
            if scan_type == "fast":
                cmd.extend(['-T4', '-F'])  # Fast scan, common ports only
            elif scan_type == "comprehensive":
                cmd.extend(['-T4', '-p-'])  # All 65535 ports
            elif scan_type == "stealth":
                cmd.extend(['-sS', '-T2'])  # Stealth SYN scan
            else:
                cmd.extend(['-T4'])  # Default timing
            
            # Port specification
            if ports:
                port_range = ','.join(map(str, ports))
                cmd.extend(['-p', port_range])
            
            # Output format and options
            cmd.extend([
                '-sV',  # Service version detection
                '-sC',  # Default scripts
                '--open',  # Only show open ports
                '-oX', '-',  # XML output to stdout
                '--host-timeout', '30s',  # 30 second host timeout
                '--max-retries', '2',  # Limit retries
                ip
            ])
            
            logger.info(f"Running Nmap scan: {' '.join(cmd)}")
            
            # Execute Nmap
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"Nmap scan failed: {result.stderr}")
                return self._fallback_socket_scan(ip, ports)
            
            # Parse XML output
            return self._parse_nmap_xml(result.stdout, ip)
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Nmap scan timeout for {ip}")
            return []
        except Exception as e:
            logger.error(f"Nmap scan error for {ip}: {e}")
            return self._fallback_socket_scan(ip, ports)
    
    def _parse_nmap_xml(self, xml_output: str, ip: str) -> List[Dict]:
        """Parse Nmap XML output into structured port data"""
        try:
            root = ET.fromstring(xml_output)
            open_ports = []
            
            # Find host element
            host = root.find('.//host')
            if host is None:
                return []
            
            # Check if host is up
            status = host.find('status')
            if status is None or status.get('state') != 'up':
                logger.info(f"Host {ip} is not responding")
                return []
            
            # Parse ports
            ports = host.find('ports')
            if ports is not None:
                for port in ports.findall('port'):
                    port_data = self._parse_port_element(port)
                    if port_data:
                        open_ports.append(port_data)
            
            logger.info(f"Nmap found {len(open_ports)} open ports on {ip}")
            return open_ports
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse Nmap XML output: {e}")
            return []
    
    def _parse_port_element(self, port_element) -> Optional[Dict]:
        """Parse individual port element from Nmap XML"""
        try:
            port_id = int(port_element.get('portid'))
            protocol = port_element.get('protocol', 'tcp').upper()
            
            # Get port state
            state = port_element.find('state')
            if state is None or state.get('state') != 'open':
                return None
            
            # Get service information
            service = port_element.find('service')
            service_name = 'unknown'
            service_product = ''
            service_version = ''
            
            if service is not None:
                service_name = service.get('name', 'unknown')
                service_product = service.get('product', '')
                service_version = service.get('version', '')
            
            # Build service description
            description = service_name
            if service_product:
                description = f"{service_product}"
                if service_version:
                    description += f" {service_version}"
            
            # Determine risk level based on port and service
            risk_level = self._assess_port_risk(port_id, service_name, protocol)
            
            return {
                'port': port_id,
                'protocol': protocol,
                'service': service_name,
                'description': description,
                'product': service_product,
                'version': service_version,
                'risk_level': risk_level,
                'state': 'open',
                'scanner': 'nmap'
            }
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing port element: {e}")
            return None
    
    def _assess_port_risk(self, port: int, service: str, protocol: str) -> str:
        """Assess security risk level of an open port"""
        
        # Critical risk ports
        critical_ports = {
            23: 'telnet',  # Unencrypted
            135: 'rpc',    # Windows RPC
            445: 'smb',    # SMB/CIFS
            3389: 'rdp',   # Remote Desktop
            1433: 'mssql', # SQL Server
            3306: 'mysql', # MySQL
            5432: 'postgresql', # PostgreSQL
        }
        
        # High risk ports
        high_risk_ports = {
            21: 'ftp',
            22: 'ssh',
            139: 'netbios',
            161: 'snmp',
            1521: 'oracle',
            27017: 'mongodb',
            6379: 'redis',
        }
        
        # Check by port number
        if port in critical_ports:
            return 'critical'
        elif port in high_risk_ports:
            return 'high'
        elif port in [80, 8080, 8000, 8008]:  # HTTP ports
            return 'medium'
        elif port in [443, 8443]:  # HTTPS ports
            return 'low'
        
        # Check by service name
        service_lower = service.lower()
        if any(term in service_lower for term in ['telnet', 'rlogin', 'rsh']):
            return 'critical'
        elif any(term in service_lower for term in ['ssh', 'ftp', 'snmp', 'sql']):
            return 'high'
        elif 'http' in service_lower and 'https' not in service_lower:
            return 'medium'
        elif 'https' in service_lower or 'ssl' in service_lower:
            return 'low'
        
        # Default based on port range
        if port < 1024:  # Well-known ports
            return 'medium'
        else:
            return 'low'
    
    def _fallback_socket_scan(self, ip: str, ports: List[int] = None) -> List[Dict]:
        """Fallback to basic socket scanning if Nmap is not available"""
        if ports is None:
            # Common ports for fallback
            ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 
                    1433, 3306, 3389, 5432, 8080, 8443]
        
        open_ports = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    service_info = self._get_basic_service_info(port)
                    open_ports.append({
                        'port': port,
                        'protocol': 'TCP',
                        'service': service_info['service'],
                        'description': service_info['description'],
                        'risk_level': service_info['risk_level'],
                        'state': 'open',
                        'scanner': 'socket'
                    })
                    
            except Exception:
                continue
        
        return open_ports
    
    def _get_basic_service_info(self, port: int) -> Dict:
        """Get basic service information for common ports"""
        port_database = {
            21: {'service': 'FTP', 'description': 'File Transfer Protocol', 'risk_level': 'high'},
            22: {'service': 'SSH', 'description': 'Secure Shell', 'risk_level': 'high'},
            23: {'service': 'Telnet', 'description': 'Telnet (INSECURE)', 'risk_level': 'critical'},
            25: {'service': 'SMTP', 'description': 'Simple Mail Transfer Protocol', 'risk_level': 'medium'},
            53: {'service': 'DNS', 'description': 'Domain Name System', 'risk_level': 'medium'},
            80: {'service': 'HTTP', 'description': 'Hypertext Transfer Protocol', 'risk_level': 'medium'},
            110: {'service': 'POP3', 'description': 'Post Office Protocol v3', 'risk_level': 'medium'},
            135: {'service': 'RPC', 'description': 'Microsoft RPC', 'risk_level': 'critical'},
            139: {'service': 'NetBIOS-SSN', 'description': 'NetBIOS Session Service', 'risk_level': 'high'},
            143: {'service': 'IMAP', 'description': 'Internet Message Access Protocol', 'risk_level': 'medium'},
            443: {'service': 'HTTPS', 'description': 'HTTP over SSL/TLS', 'risk_level': 'low'},
            445: {'service': 'SMB', 'description': 'Server Message Block', 'risk_level': 'critical'},
            993: {'service': 'IMAPS', 'description': 'IMAP over SSL', 'risk_level': 'low'},
            995: {'service': 'POP3S', 'description': 'POP3 over SSL', 'risk_level': 'low'},
            1433: {'service': 'MSSQL', 'description': 'Microsoft SQL Server', 'risk_level': 'critical'},
            3306: {'service': 'MySQL', 'description': 'MySQL Database', 'risk_level': 'critical'},
            3389: {'service': 'RDP', 'description': 'Remote Desktop Protocol', 'risk_level': 'critical'},
            5432: {'service': 'PostgreSQL', 'description': 'PostgreSQL Database', 'risk_level': 'critical'},
            8080: {'service': 'HTTP-Alt', 'description': 'Alternative HTTP port', 'risk_level': 'medium'},
            8443: {'service': 'HTTPS-Alt', 'description': 'Alternative HTTPS port', 'risk_level': 'low'},
        }
        
        return port_database.get(port, {
            'service': f'Port-{port}',
            'description': f'Unknown service on port {port}',
            'risk_level': 'medium'
        })
    
    def quick_scan(self, ip: str) -> List[Dict]:
        """Quick scan of most common ports"""
        if self.nmap_available:
            return self.scan_ports_nmap(ip, scan_type="fast")
        else:
            common_ports = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445, 1433, 3306, 3389, 8080]
            return self._fallback_socket_scan(ip, common_ports)
    
    def comprehensive_scan(self, ip: str) -> List[Dict]:
        """Comprehensive scan of many ports"""
        if self.nmap_available:
            # Use Nmap's top 1000 ports
            return self.scan_ports_nmap(ip, scan_type="comprehensive")
        else:
            # Extended port list for socket fallback
            extended_ports = [
                21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995,
                1433, 3306, 3389, 5432, 8080, 8443, 161, 162, 389, 636, 1521,
                27017, 6379, 5985, 5986, 8000, 8001, 8008, 8081, 8082, 8090,
                9000, 9001, 9090, 3000, 4000, 5000, 8888, 10050, 10051
            ]
            return self._fallback_socket_scan(ip, extended_ports)
    
    def get_scanner_info(self) -> Dict:
        """Get information about the scanner capabilities"""
        return {
            'nmap_available': self.nmap_available,
            'scanner_type': 'nmap' if self.nmap_available else 'socket',
            'capabilities': {
                'service_detection': self.nmap_available,
                'version_detection': self.nmap_available,
                'os_detection': self.nmap_available,
                'script_scanning': self.nmap_available,
                'stealth_scanning': self.nmap_available
            }
        } 