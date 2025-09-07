"""
Enhanced Security Event Descriptions
Professional, detailed descriptions for security events
"""

import random

class SecurityEventDescriptions:
    """Professional security event description generator"""
    
    THREAT_DESCRIPTIONS = {
        'device_threat_detected': {
            'critical': [
                {
                    'title': 'Critical Malware Infection Detected',
                    'description': 'CRITICAL ALERT: Device {ip} ({hostname}) has been identified as infected with advanced malware. The malware is actively communicating with command & control servers, attempting to steal sensitive data, and spreading laterally across the network. IMMEDIATE ISOLATION REQUIRED.',
                    'details': {
                        'threat_type': 'Advanced Persistent Threat (APT)',
                        'indicators': ['C2 communication', 'Data exfiltration', 'Lateral movement'],
                        'risk_level': 'CRITICAL - Network-wide compromise possible',
                        'immediate_actions': [
                            'Isolate device from network immediately',
                            'Run full antivirus scan',
                            'Check for data exfiltration',
                            'Scan connected devices'
                        ],
                        'technical_details': 'Detected encrypted communications to known malicious IPs, suspicious process injections, and unauthorized network scanning activities'
                    }
                },
                {
                    'title': 'Ransomware Activity Detected',
                    'description': 'RANSOMWARE ALERT: Device {ip} ({hostname}) is showing signs of ransomware infection. File encryption activities detected along with suspicious network communications. The device is attempting to encrypt local files and may spread to network shares. IMMEDIATE ACTION REQUIRED.',
                    'details': {
                        'threat_type': 'Ransomware',
                        'indicators': ['File encryption', 'Suspicious processes', 'Network propagation'],
                        'risk_level': 'CRITICAL - Data loss imminent',
                        'immediate_actions': [
                            'Disconnect from network IMMEDIATELY',
                            'Do not restart the device',
                            'Contact IT security team',
                            'Prepare for data recovery'
                        ],
                        'technical_details': 'Mass file modification patterns detected, suspicious executable behavior, and network share enumeration activities'
                    }
                }
            ],
            'high': [
                {
                    'title': 'Suspicious Network Behavior Detected',
                    'description': 'HIGH PRIORITY: Device {ip} ({hostname}) is exhibiting suspicious network behavior including unusual outbound connections, abnormal data transfer patterns, and communication with potentially malicious domains. This may indicate malware infection or unauthorized access.',
                    'details': {
                        'threat_type': 'Suspicious Network Activity',
                        'indicators': ['Unusual outbound traffic', 'Suspicious domains', 'Abnormal data patterns'],
                        'risk_level': 'HIGH - Potential compromise',
                        'recommended_actions': [
                            'Monitor network traffic closely',
                            'Run security scan on device',
                            'Check user activity logs',
                            'Consider temporary isolation'
                        ],
                        'technical_details': 'Detected connections to newly registered domains, unusual DNS queries, and traffic patterns inconsistent with normal usage'
                    }
                },
                {
                    'title': 'Unauthorized Access Attempt',
                    'description': 'SECURITY BREACH: Multiple unauthorized access attempts detected on device {ip} ({hostname}). An attacker is attempting to gain access using various credential combinations and exploitation techniques. The device may be under active attack.',
                    'details': {
                        'threat_type': 'Brute Force Attack',
                        'indicators': ['Multiple login failures', 'Credential stuffing', 'Exploitation attempts'],
                        'risk_level': 'HIGH - Active attack in progress',
                        'recommended_actions': [
                            'Enable account lockout policies',
                            'Monitor authentication logs',
                            'Implement IP blocking',
                            'Review user accounts'
                        ],
                        'technical_details': 'Over 100 failed authentication attempts in the last hour from multiple source IPs using automated tools'
                    }
                }
            ],
            'medium': [
                {
                    'title': 'Anomalous Device Behavior',
                    'description': 'MONITORING ALERT: Device {ip} ({hostname}) is showing behavior that deviates from its normal patterns. This includes unusual network connections, unexpected service activations, or abnormal resource usage. Investigation recommended.',
                    'details': {
                        'threat_type': 'Behavioral Anomaly',
                        'indicators': ['Unusual patterns', 'Service changes', 'Resource anomalies'],
                        'risk_level': 'MEDIUM - Requires investigation',
                        'recommended_actions': [
                            'Review recent changes',
                            'Check installed software',
                            'Monitor user activity',
                            'Verify system integrity'
                        ],
                        'technical_details': 'Device behavior has deviated significantly from established baseline patterns over the past 24 hours'
                    }
                }
            ],
            'low': [
                {
                    'title': 'Minor Security Anomaly',
                    'description': 'INFORMATIONAL: Device {ip} ({hostname}) has triggered a low-priority security alert. This may be due to software updates, configuration changes, or normal operational variations. Monitoring continues.',
                    'details': {
                        'threat_type': 'Minor Anomaly',
                        'indicators': ['Configuration changes', 'Software updates', 'Normal variations'],
                        'risk_level': 'LOW - Informational only',
                        'recommended_actions': [
                            'Continue monitoring',
                            'Document changes',
                            'No immediate action required'
                        ],
                        'technical_details': 'Minor deviation from normal patterns detected, likely due to legitimate system changes'
                    }
                }
            ]
        },
        'port_scan': {
            'critical': [
                {
                    'title': 'Aggressive Port Scan Attack',
                    'description': 'CRITICAL THREAT: An aggressive port scan is targeting device {ip} ({hostname}). The attacker is systematically probing all ports to identify vulnerabilities and open services. This is typically the first phase of a targeted attack.',
                    'details': {
                        'threat_type': 'Network Reconnaissance',
                        'indicators': ['Systematic port probing', 'Service enumeration', 'Vulnerability scanning'],
                        'risk_level': 'CRITICAL - Attack preparation phase',
                        'immediate_actions': [
                            'Block source IP immediately',
                            'Enable intrusion prevention',
                            'Review firewall rules',
                            'Monitor for follow-up attacks'
                        ],
                        'technical_details': 'Comprehensive scan detected covering ports 1-65535 with advanced evasion techniques'
                    }
                }
            ],
            'high': [
                {
                    'title': 'Targeted Port Scanning',
                    'description': 'HIGH ALERT: Targeted port scanning detected against device {ip} ({hostname}). The scan is focusing on specific service ports including SSH, RDP, and web services. This indicates reconnaissance for a potential targeted attack.',
                    'details': {
                        'threat_type': 'Targeted Reconnaissance',
                        'indicators': ['Focused port scanning', 'Service identification', 'Attack preparation'],
                        'risk_level': 'HIGH - Targeted attack likely',
                        'recommended_actions': [
                            'Implement rate limiting',
                            'Monitor authentication attempts',
                            'Review exposed services',
                            'Consider IP blocking'
                        ],
                        'technical_details': 'Scan targeting critical service ports: 22 (SSH), 3389 (RDP), 80/443 (HTTP/HTTPS), 21 (FTP)'
                    }
                }
            ]
        },
        'unauthorized_access': {
            'critical': [
                {
                    'title': 'Successful Unauthorized Access',
                    'description': 'SECURITY BREACH: Unauthorized access has been gained to device {ip} ({hostname}). An attacker has successfully bypassed authentication and is now inside the system. IMMEDIATE CONTAINMENT REQUIRED.',
                    'details': {
                        'threat_type': 'Security Breach',
                        'indicators': ['Successful unauthorized login', 'Privilege escalation', 'System access'],
                        'risk_level': 'CRITICAL - System compromised',
                        'immediate_actions': [
                            'Isolate device immediately',
                            'Change all passwords',
                            'Review system logs',
                            'Initiate incident response'
                        ],
                        'technical_details': 'Unauthorized user session detected with administrative privileges and suspicious command execution'
                    }
                }
            ]
        },
        'port_opening': {
            'high': [
                {
                    'title': 'Unauthorized Port Opening',
                    'description': 'SECURITY ALERT: An unauthorized port has been opened on device {ip} ({hostname}). Port {port} is now listening for incoming connections without proper authorization. This may indicate malware installation or system compromise.',
                    'details': {
                        'threat_type': 'Unauthorized Service',
                        'indicators': ['Unauthorized port opening', 'New service activation', 'Configuration tampering'],
                        'risk_level': 'HIGH - Potential backdoor',
                        'recommended_actions': [
                            'Identify the service using the port',
                            'Check for unauthorized software',
                            'Review system changes',
                            'Consider blocking the port'
                        ],
                        'technical_details': 'Port opened without authorization, potentially creating backdoor access'
                    }
                }
            ]
        }
    }
    
    @classmethod
    def get_enhanced_description(cls, event_type, severity, device_ip, hostname=None, **kwargs):
        """Get enhanced description for a security event"""
        hostname = hostname or 'Unknown Device'
        
        if event_type in cls.THREAT_DESCRIPTIONS:
            severity_descriptions = cls.THREAT_DESCRIPTIONS[event_type].get(severity, [])
            if severity_descriptions:
                enhanced = random.choice(severity_descriptions)
                
                # Format the description with device information
                formatted_description = enhanced['description'].format(
                    ip=device_ip,
                    hostname=hostname,
                    port=kwargs.get('port', random.choice([22, 80, 443, 3389, 21, 23, 25, 53]))
                )
                
                return {
                    'title': enhanced['title'],
                    'description': formatted_description,
                    'details': enhanced['details']
                }
        
        # Fallback for unknown event types
        return {
            'title': f'Security Event: {event_type.replace("_", " ").title()}',
            'description': f'Security event detected on device {device_ip} ({hostname}). Please investigate this activity.',
            'details': {
                'threat_type': 'Unknown',
                'risk_level': f'{severity.upper()} - Requires investigation',
                'recommended_actions': ['Investigate the event', 'Review system logs', 'Monitor device activity']
            }
        } 