from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class NetworkInterface(models.Model):
    """Network interface model"""
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True)
    is_active = models.BooleanField(default=True)
    interface_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'ip_address']

    def __str__(self):
        return f"{self.name} - {self.ip_address}"


class NetworkDevice(models.Model):
    """Discovered network device model"""
    DEVICE_TYPES = [
        ('router', 'Router'),
        ('switch', 'Switch'),
        ('computer', 'Computer'),
        ('mobile', 'Mobile Device'),
        ('printer', 'Printer'),
        ('iot', 'IoT Device'),
        ('server', 'Server'),
        ('unknown', 'Unknown'),
    ]

    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('unknown', 'Unknown'),
    ]

    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=17, blank=True)
    hostname = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='unknown')
    manufacturer = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown')
    last_seen = models.DateTimeField(default=timezone.now)
    first_seen = models.DateTimeField(auto_now_add=True)
    open_ports = models.JSONField(default=list, blank=True)
    os_info = models.TextField(blank=True)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds
    is_monitored = models.BooleanField(default=True)
    
    # Real-time monitoring fields
    uptime_percentage = models.FloatField(default=0.0)  # Percentage uptime
    total_downtime = models.IntegerField(default=0)  # Total downtime in seconds
    avg_response_time = models.FloatField(default=0.0)  # Average response time
    packet_loss_rate = models.FloatField(default=0.0)  # Packet loss percentage
    last_ping_time = models.DateTimeField(null=True, blank=True)
    ping_success_count = models.IntegerField(default=0)
    ping_failure_count = models.IntegerField(default=0)
    
    # Traffic monitoring
    total_bytes_in = models.BigIntegerField(default=0)
    total_bytes_out = models.BigIntegerField(default=0)
    current_bandwidth_usage = models.FloatField(default=0.0)  # Current usage in Mbps
    
    # Security & service monitoring
    services_running = models.JSONField(default=list, blank=True)  # Current running services
    security_score = models.IntegerField(default=100)  # 0-100 security score
    vulnerability_count = models.IntegerField(default=0)
    last_port_scan = models.DateTimeField(null=True, blank=True)
    
    # Real-time status tracking
    is_scanning = models.BooleanField(default=False)  # Currently being scanned
    scan_progress = models.IntegerField(default=0)  # Scan progress percentage
    monitor_enabled = models.BooleanField(default=True)  # Enable real-time monitoring
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_seen']

    def __str__(self):
        return f"{self.ip_address} ({self.hostname or 'Unknown'})"

    @property
    def is_online(self):
        """Check if device was seen recently (within last 5 minutes)"""
        return (timezone.now() - self.last_seen).seconds < 300

    def add_open_port(self, port, service=None):
        """Add an open port to the device"""
        port_info = {'port': port, 'service': service, 'discovered_at': timezone.now().isoformat()}
        if port_info not in self.open_ports:
            self.open_ports.append(port_info)
            self.save()

    def update_ping_stats(self, success=True, response_time=None):
        """Update ping statistics for the device"""
        if success:
            self.ping_success_count += 1
            if response_time:
                # Calculate running average of response time
                total_pings = self.ping_success_count + self.ping_failure_count
                if total_pings > 1:
                    self.avg_response_time = (
                        (self.avg_response_time * (total_pings - 1) + response_time) / total_pings
                    )
                else:
                    self.avg_response_time = response_time
                self.response_time = response_time
        else:
            self.ping_failure_count += 1
        
        # Update packet loss rate
        total_pings = self.ping_success_count + self.ping_failure_count
        if total_pings > 0:
            self.packet_loss_rate = (self.ping_failure_count / total_pings) * 100
        
        self.last_ping_time = timezone.now()
        self.save()

    def calculate_uptime_percentage(self):
        """Calculate uptime percentage based on historical data"""
        total_time = (timezone.now() - self.first_seen).total_seconds()
        if total_time > 0:
            self.uptime_percentage = max(0, (total_time - self.total_downtime) / total_time * 100)
        self.save()


class DeviceStatusHistory(models.Model):
    """Historical status tracking for devices"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='status_history')
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=NetworkDevice.STATUS_CHOICES)
    response_time = models.FloatField(null=True, blank=True)
    uptime_at_time = models.FloatField(default=0.0)
    packet_loss_at_time = models.FloatField(default=0.0)
    
    # Event that triggered this status change
    trigger_event = models.CharField(max_length=50, choices=[
        ('ping_success', 'Ping Success'),
        ('ping_failure', 'Ping Failure'),
        ('port_scan', 'Port Scan'),
        ('traffic_analysis', 'Traffic Analysis'),
        ('manual_check', 'Manual Check'),
        ('system_startup', 'System Startup'),
    ], default='ping_success')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.ip_address} - {self.status} at {self.timestamp}"


class NetworkScan(models.Model):
    """Advanced network scan session model with comprehensive scanning capabilities"""
    
    SCAN_TYPES = [
        ('ping_sweep', 'Ping Sweep'),
        ('port_scan', 'Port Scan'),
        ('service_detection', 'Service Detection'),
        ('os_fingerprinting', 'OS Fingerprinting'),
        ('vulnerability_scan', 'Vulnerability Scan'),
        ('discovery', 'Network Discovery'),
        ('stealth_scan', 'Stealth Scan'),
        ('comprehensive', 'Comprehensive Scan'),
        ('custom', 'Custom Scan'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initializing', 'Initializing'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('timeout', 'Timeout'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('normal', 'Normal Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical Priority'),
    ]

    SCAN_TECHNIQUES = [
        ('tcp_connect', 'TCP Connect'),
        ('tcp_syn', 'TCP SYN Stealth'),
        ('tcp_fin', 'TCP FIN'),
        ('tcp_null', 'TCP NULL'),
        ('tcp_xmas', 'TCP XMAS'),
        ('udp', 'UDP Scan'),
        ('icmp', 'ICMP Ping'),
        ('arp', 'ARP Ping'),
        ('tcp_ack', 'TCP ACK'),
    ]

    # Basic scan information
    scan_id = models.CharField(max_length=36, unique=True)  # UUID
    name = models.CharField(max_length=200, blank=True)  # User-friendly name
    description = models.TextField(blank=True)
    scan_type = models.CharField(max_length=30, choices=SCAN_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Target configuration
    target_range = models.CharField(max_length=200)  # e.g., "192.168.1.0/24" or "192.168.1.1-50"
    target_ports = models.CharField(max_length=1000, blank=True)  # e.g., "22,80,443,1000-2000"
    exclude_hosts = models.CharField(max_length=500, blank=True)  # Hosts to exclude
    
    # Scan configuration
    scan_techniques = models.JSONField(default=list, blank=True)  # List of techniques to use
    timing_template = models.CharField(max_length=20, choices=[
        ('paranoid', 'Paranoid (T0)'),
        ('sneaky', 'Sneaky (T1)'),
        ('polite', 'Polite (T2)'),
        ('normal', 'Normal (T3)'),
        ('aggressive', 'Aggressive (T4)'),
        ('insane', 'Insane (T5)'),
    ], default='normal')
    
    # Advanced options
    max_retries = models.IntegerField(default=3)
    timeout_per_host = models.IntegerField(default=30)  # seconds
    max_parallel_hosts = models.IntegerField(default=50)
    max_parallel_ports = models.IntegerField(default=100)
    randomize_hosts = models.BooleanField(default=True)
    fragment_packets = models.BooleanField(default=False)
    spoof_source_ip = models.CharField(max_length=45, blank=True)
    
    # Service detection options
    service_detection = models.BooleanField(default=True)
    version_detection = models.BooleanField(default=True)
    os_detection = models.BooleanField(default=False)
    script_scanning = models.BooleanField(default=False)
    aggressive_scan = models.BooleanField(default=False)
    
    # Status and execution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    current_phase = models.CharField(max_length=100, blank=True)
    current_target = models.CharField(max_length=100, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    # Results and statistics
    total_hosts_scanned = models.IntegerField(default=0)
    hosts_up = models.IntegerField(default=0)
    hosts_down = models.IntegerField(default=0)
    total_ports_scanned = models.IntegerField(default=0)
    open_ports_found = models.IntegerField(default=0)
    services_detected = models.IntegerField(default=0)
    vulnerabilities_found = models.IntegerField(default=0)
    
    # Detailed results
    scan_results = models.JSONField(default=dict, blank=True)  # Comprehensive scan results
    host_results = models.JSONField(default=list, blank=True)  # Per-host results
    port_results = models.JSONField(default=list, blank=True)  # Per-port results
    service_results = models.JSONField(default=list, blank=True)  # Service detection results
    vulnerability_results = models.JSONField(default=list, blank=True)  # Vulnerability scan results
    
    # Performance metrics
    scan_rate = models.FloatField(default=0.0)  # Hosts/ports per second
    bandwidth_used = models.FloatField(default=0.0)  # MB
    cpu_usage_avg = models.FloatField(default=0.0)  # Percentage
    memory_usage_peak = models.FloatField(default=0.0)  # MB
    
    # Error handling and logging
    errors_count = models.IntegerField(default=0)
    warnings_count = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
    debug_log = models.TextField(blank=True)
    
    # Scheduling and automation
    is_scheduled = models.BooleanField(default=False)
    schedule_cron = models.CharField(max_length=100, blank=True)  # Cron expression
    next_run = models.DateTimeField(null=True, blank=True)
    auto_retry_on_failure = models.BooleanField(default=False)
    max_auto_retries = models.IntegerField(default=3)
    retry_count = models.IntegerField(default=0)
    
    # Reporting and export
    generate_report = models.BooleanField(default=True)
    report_format = models.CharField(max_length=20, choices=[
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('html', 'HTML'),
    ], default='json')
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)  # User-defined tags
    metadata = models.JSONField(default=dict, blank=True)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['scan_type', '-started_at']),
            models.Index(fields=['started_by', '-started_at']),
            models.Index(fields=['priority', '-started_at']),
        ]

    def __str__(self):
        name = self.name or f"{self.scan_type.replace('_', ' ').title()} Scan"
        return f"{name} - {self.target_range} ({self.status})"

    @property
    def duration(self):
        """Calculate scan duration"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.status in ['running', 'paused']:
            return (timezone.now() - self.started_at).total_seconds()
        return None

    @property
    def duration_formatted(self):
        """Get formatted duration string"""
        duration = self.duration
        if duration is None:
            return "N/A"
        
        hours, remainder = divmod(int(duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @property
    def success_rate(self):
        """Calculate scan success rate"""
        if self.total_hosts_scanned == 0:
            return 0.0
        return (self.hosts_up / self.total_hosts_scanned) * 100

    @property
    def port_discovery_rate(self):
        """Calculate port discovery rate"""
        if self.total_ports_scanned == 0:
            return 0.0
        return (self.open_ports_found / self.total_ports_scanned) * 100

    @property
    def estimated_time_remaining(self):
        """Estimate time remaining for scan"""
        if self.status != 'running' or self.progress_percentage == 0:
            return None
        
        elapsed = self.duration
        if elapsed and self.progress_percentage > 0:
            total_estimated = elapsed / (self.progress_percentage / 100)
            remaining = total_estimated - elapsed
            return max(0, remaining)
        return None

    @property
    def risk_score(self):
        """Calculate risk score based on findings"""
        score = 0
        
        # Base score from open ports
        if self.open_ports_found > 0:
            score += min(self.open_ports_found * 2, 30)
        
        # Add score for services
        if self.services_detected > 0:
            score += min(self.services_detected * 3, 25)
        
        # Add score for vulnerabilities
        if self.vulnerabilities_found > 0:
            score += min(self.vulnerabilities_found * 10, 45)
        
        return min(score, 100)

    def get_scan_summary(self):
        """Get comprehensive scan summary"""
        return {
            'scan_info': {
                'id': self.scan_id,
                'name': self.name or f"{self.scan_type.replace('_', ' ').title()} Scan",
                'type': self.scan_type,
                'status': self.status,
                'priority': self.priority,
                'duration': self.duration_formatted,
                'progress': self.progress_percentage,
            },
            'targets': {
                'range': self.target_range,
                'ports': self.target_ports or 'Default',
                'excluded': self.exclude_hosts or 'None',
            },
            'results': {
                'hosts_scanned': self.total_hosts_scanned,
                'hosts_up': self.hosts_up,
                'hosts_down': self.hosts_down,
                'success_rate': f"{self.success_rate:.1f}%",
                'ports_scanned': self.total_ports_scanned,
                'open_ports': self.open_ports_found,
                'discovery_rate': f"{self.port_discovery_rate:.1f}%",
                'services_detected': self.services_detected,
                'vulnerabilities': self.vulnerabilities_found,
                'risk_score': self.risk_score,
            },
            'performance': {
                'scan_rate': f"{self.scan_rate:.2f} hosts/sec",
                'bandwidth_used': f"{self.bandwidth_used:.2f} MB",
                'cpu_usage': f"{self.cpu_usage_avg:.1f}%",
                'memory_peak': f"{self.memory_usage_peak:.1f} MB",
            },
            'issues': {
                'errors': self.errors_count,
                'warnings': self.warnings_count,
            }
        }

    def pause(self):
        """Pause the scan"""
        if self.status == 'running':
            self.status = 'paused'
            self.paused_at = timezone.now()
            self.save()

    def resume(self):
        """Resume the scan"""
        if self.status == 'paused':
            self.status = 'running'
            self.paused_at = None
            self.save()

    def cancel(self):
        """Cancel the scan"""
        if self.status in ['pending', 'running', 'paused']:
            self.status = 'cancelled'
            self.completed_at = timezone.now()
            self.save()

    def mark_completed(self):
        """Mark scan as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()

    def mark_failed(self, error_message=None):
        """Mark scan as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_message:
            self.error_log += f"\n{timezone.now()}: {error_message}"
        self.save()

    def add_error(self, error_message):
        """Add an error to the scan log"""
        self.errors_count += 1
        self.error_log += f"\n{timezone.now()}: ERROR - {error_message}"
        self.save()

    def add_warning(self, warning_message):
        """Add a warning to the scan log"""
        self.warnings_count += 1
        self.error_log += f"\n{timezone.now()}: WARNING - {warning_message}"
        self.save()

    def update_progress(self, percentage, phase=None, target=None):
        """Update scan progress"""
        self.progress_percentage = min(100, max(0, percentage))
        if phase:
            self.current_phase = phase
        if target:
            self.current_target = target
        
        # Update estimated completion
        if self.progress_percentage > 0 and self.status == 'running':
            elapsed = self.duration
            if elapsed:
                total_estimated = elapsed / (self.progress_percentage / 100)
                self.estimated_completion = self.started_at + timezone.timedelta(seconds=total_estimated)
        
        self.save()


class ScanTemplate(models.Model):
    """Predefined scan templates for common scanning scenarios"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    scan_type = models.CharField(max_length=30, choices=NetworkScan.SCAN_TYPES)
    
    # Template configuration
    default_ports = models.CharField(max_length=1000, blank=True)
    scan_techniques = models.JSONField(default=list, blank=True)
    timing_template = models.CharField(max_length=20, default='normal')
    service_detection = models.BooleanField(default=True)
    version_detection = models.BooleanField(default=False)
    os_detection = models.BooleanField(default=False)
    script_scanning = models.BooleanField(default=False)
    
    # Advanced settings
    max_parallel_hosts = models.IntegerField(default=50)
    timeout_per_host = models.IntegerField(default=30)
    
    # Metadata
    is_builtin = models.BooleanField(default=False)  # Built-in templates cannot be deleted
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def create_scan(self, target_range, user=None, **overrides):
        """Create a new scan based on this template"""
        import uuid
        
        scan_data = {
            'scan_id': str(uuid.uuid4()),
            'name': overrides.get('name', f"{self.name} - {target_range}"),
            'scan_type': self.scan_type,
            'target_range': target_range,
            'target_ports': overrides.get('target_ports', self.default_ports),
            'scan_techniques': overrides.get('scan_techniques', self.scan_techniques),
            'timing_template': overrides.get('timing_template', self.timing_template),
            'service_detection': overrides.get('service_detection', self.service_detection),
            'version_detection': overrides.get('version_detection', self.version_detection),
            'os_detection': overrides.get('os_detection', self.os_detection),
            'script_scanning': overrides.get('script_scanning', self.script_scanning),
            'max_parallel_hosts': overrides.get('max_parallel_hosts', self.max_parallel_hosts),
            'timeout_per_host': overrides.get('timeout_per_host', self.timeout_per_host),
            'started_by': user,
        }
        
        # Apply any additional overrides
        scan_data.update(overrides)
        
        return NetworkScan.objects.create(**scan_data)


class NetworkTraffic(models.Model):
    """Network traffic monitoring model"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='traffic')
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Traffic data
    bytes_sent = models.BigIntegerField(default=0)
    bytes_received = models.BigIntegerField(default=0)
    packets_sent = models.IntegerField(default=0)
    packets_received = models.IntegerField(default=0)
    
    # Connection info
    active_connections = models.IntegerField(default=0)
    bandwidth_usage = models.FloatField(default=0.0)  # Percentage
    
    class Meta:
        ordering = ['-timestamp']
        unique_together = ['device', 'timestamp']

    def __str__(self):
        return f"Traffic for {self.device.ip_address} at {self.timestamp}"

    @property
    def total_bytes(self):
        return self.bytes_sent + self.bytes_received

    @property
    def total_packets(self):
        return self.packets_sent + self.packets_received


class SecurityEvent(models.Model):
    """Security events and alerts model"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    EVENT_TYPES = [
        ('port_scan', 'Port Scan Detected'),
        ('unusual_traffic', 'Unusual Traffic Pattern'),
        ('new_device', 'New Device Detected'),
        ('device_offline', 'Device Went Offline'),
        ('failed_connection', 'Failed Connection Attempts'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('device_threat_detected', 'Device Threat Detected'),
        ('high_bandwidth_usage', 'High Bandwidth Usage'),
        ('high_packet_rate', 'High Packet Rate'),
        ('high_cpu_usage', 'High CPU Usage'),
        ('ip_change', 'IP Address Changed'),
        ('port_opened', 'Port Opened'),
        ('port_closed', 'Port Closed'),
    ]

    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    source_device = models.ForeignKey(
        NetworkDevice, 
        on_delete=models.CASCADE, 
        related_name='security_events_as_source',
        null=True, 
        blank=True
    )
    target_device = models.ForeignKey(
        NetworkDevice, 
        on_delete=models.CASCADE, 
        related_name='security_events_as_target',
        null=True, 
        blank=True
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Event details
    details = models.JSONField(default=dict, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.timestamp}"

    def resolve(self, user=None):
        """Mark event as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()


class NetworkConfiguration(models.Model):
    """Network monitoring configuration"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Scan settings
    auto_scan_enabled = models.BooleanField(default=True)
    scan_interval = models.IntegerField(default=300)  # seconds
    scan_range = models.CharField(max_length=100, default="192.168.1.0/24")
    
    # Monitoring settings
    traffic_monitoring = models.BooleanField(default=True)
    security_monitoring = models.BooleanField(default=True)
    packet_capture = models.BooleanField(default=False)
    
    # Alert settings
    alert_on_new_devices = models.BooleanField(default=True)
    alert_on_device_offline = models.BooleanField(default=True)
    alert_on_port_scan = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def activate(self):
        """Activate this configuration and deactivate others"""
        NetworkConfiguration.objects.update(is_active=False)
        self.is_active = True
        self.save() 