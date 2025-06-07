from rest_framework import serializers
from django.contrib.auth.models import User
from apps.network_monitor.models import (
    NetworkDevice, NetworkScan, NetworkTraffic, 
    SecurityEvent, NetworkInterface, NetworkConfiguration, ScanTemplate
)


class NetworkInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkInterface
        fields = '__all__'


class NetworkDeviceSerializer(serializers.ModelSerializer):
    is_online = serializers.ReadOnlyField()
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = NetworkDevice
        fields = [
            'id', 'ip_address', 'mac_address', 'hostname', 'device_type', 
            'device_type_display', 'manufacturer', 'status', 'status_display',
            'last_seen', 'first_seen', 'open_ports', 'os_info', 'response_time',
            'is_monitored', 'metadata', 'is_online', 'created_at', 'updated_at'
        ]
        read_only_fields = ['first_seen', 'created_at', 'updated_at']


class NetworkDeviceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkDevice
        fields = [
            'ip_address', 'mac_address', 'hostname', 'device_type',
            'manufacturer', 'is_monitored'
        ]


class NetworkScanSerializer(serializers.ModelSerializer):
    scan_type_display = serializers.CharField(source='get_scan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    timing_template_display = serializers.CharField(source='get_timing_template_display', read_only=True)
    started_by_username = serializers.CharField(source='started_by.username', read_only=True)
    
    # Computed fields
    duration = serializers.ReadOnlyField()
    duration_formatted = serializers.ReadOnlyField()
    success_rate = serializers.ReadOnlyField()
    port_discovery_rate = serializers.ReadOnlyField()
    estimated_time_remaining = serializers.ReadOnlyField()
    risk_score = serializers.ReadOnlyField()
    scan_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = NetworkScan
        fields = [
            # Basic info
            'id', 'scan_id', 'name', 'description', 'scan_type', 'scan_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            
            # Target configuration
            'target_range', 'target_ports', 'exclude_hosts',
            
            # Scan configuration
            'scan_techniques', 'timing_template', 'timing_template_display',
            'max_retries', 'timeout_per_host', 'max_parallel_hosts', 'max_parallel_ports',
            'randomize_hosts', 'fragment_packets', 'spoof_source_ip',
            
            # Service detection options
            'service_detection', 'version_detection', 'os_detection', 
            'script_scanning', 'aggressive_scan',
            
            # Status and execution
            'started_by', 'started_by_username', 'started_at', 'completed_at', 'paused_at',
            
            # Progress tracking
            'progress_percentage', 'current_phase', 'current_target', 'estimated_completion',
            
            # Results and statistics
            'total_hosts_scanned', 'hosts_up', 'hosts_down', 'total_ports_scanned',
            'open_ports_found', 'services_detected', 'vulnerabilities_found',
            
            # Detailed results
            'scan_results', 'host_results', 'port_results', 'service_results', 'vulnerability_results',
            
            # Performance metrics
            'scan_rate', 'bandwidth_used', 'cpu_usage_avg', 'memory_usage_peak',
            
            # Error handling
            'errors_count', 'warnings_count', 'error_log', 'debug_log',
            
            # Scheduling
            'is_scheduled', 'schedule_cron', 'next_run', 'auto_retry_on_failure',
            'max_auto_retries', 'retry_count',
            
            # Reporting
            'generate_report', 'report_format',
            
            # Metadata
            'tags', 'metadata', 'created_at', 'updated_at',
            
            # Computed fields
            'duration', 'duration_formatted', 'success_rate', 'port_discovery_rate',
            'estimated_time_remaining', 'risk_score', 'scan_summary'
        ]
        read_only_fields = [
            'scan_id', 'started_by', 'started_at', 'completed_at', 'paused_at',
            'progress_percentage', 'current_phase', 'current_target', 'estimated_completion',
            'total_hosts_scanned', 'hosts_up', 'hosts_down', 'total_ports_scanned',
            'open_ports_found', 'services_detected', 'vulnerabilities_found',
            'scan_results', 'host_results', 'port_results', 'service_results', 'vulnerability_results',
            'scan_rate', 'bandwidth_used', 'cpu_usage_avg', 'memory_usage_peak',
            'errors_count', 'warnings_count', 'error_log', 'debug_log',
            'retry_count', 'created_at', 'updated_at'
        ]
    
    def get_scan_summary(self, obj):
        """Get comprehensive scan summary"""
        return obj.get_scan_summary()


class NetworkScanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new network scans"""
    
    class Meta:
        model = NetworkScan
        fields = [
            # Basic info
            'name', 'description', 'scan_type', 'priority',
            
            # Target configuration
            'target_range', 'target_ports', 'exclude_hosts',
            
            # Scan configuration
            'scan_techniques', 'timing_template', 'max_retries', 'timeout_per_host',
            'max_parallel_hosts', 'max_parallel_ports', 'randomize_hosts',
            'fragment_packets', 'spoof_source_ip',
            
            # Service detection options
            'service_detection', 'version_detection', 'os_detection',
            'script_scanning', 'aggressive_scan',
            
            # Scheduling
            'is_scheduled', 'schedule_cron', 'auto_retry_on_failure', 'max_auto_retries',
            
            # Reporting
            'generate_report', 'report_format',
            
            # Metadata
            'tags', 'metadata'
        ]
    
    def validate_target_range(self, value):
        """Validate target range format"""
        if not value:
            raise serializers.ValidationError("Target range is required")
        
        # Clean up the value by removing extra spaces
        value = value.strip()
        
        # Basic validation for common formats
        import re
        import ipaddress
        
        try:
            # Try CIDR notation first (192.168.1.0/24)
            cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
            if re.match(cidr_pattern, value):
                # Validate it's a proper network
                ipaddress.IPv4Network(value, strict=False)
                return value
            
            # Try IP range with spaces (192.168.1.0 - 192.168.1.25)
            range_with_spaces_pattern = r'^(\d{1,3}\.){3}\d{1,3}\s*-\s*(\d{1,3}\.){3}\d{1,3}$'
            if re.match(range_with_spaces_pattern, value):
                # Validate both IPs are valid
                start_ip, end_ip = [ip.strip() for ip in value.split('-')]
                ipaddress.IPv4Address(start_ip)
                ipaddress.IPv4Address(end_ip)
                return value
            
            # Try short range format (192.168.1.1-50 or 192.168.1.1 - 50)
            short_range_pattern = r'^(\d{1,3}\.){3}\d{1,3}\s*-\s*\d{1,3}$'
            if re.match(short_range_pattern, value):
                # Validate base IP and range
                parts = value.split('-')
                base_ip = parts[0].strip()
                end_num = int(parts[1].strip())
                ipaddress.IPv4Address(base_ip)
                if end_num > 255:
                    raise serializers.ValidationError("End range cannot exceed 255")
                return value
            
            # Try single IP
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, value):
                ipaddress.IPv4Address(value)
                return value
            
            # Try comma-separated IPs
            if ',' in value:
                ips = [ip.strip() for ip in value.split(',')]
                for ip in ips:
                    ipaddress.IPv4Address(ip)
                return value
            
        except (ipaddress.AddressValueError, ValueError, IndexError) as e:
            raise serializers.ValidationError(
                f"Invalid IP address in target range: {str(e)}"
            )
        
        # If none of the patterns match
        raise serializers.ValidationError(
            "Invalid target range format. Supported formats:\n"
            "- CIDR: 192.168.1.0/24\n"
            "- IP Range: 192.168.1.1-192.168.1.50 or 192.168.1.1 - 192.168.1.50\n"  
            "- Short Range: 192.168.1.1-50\n"
            "- Single IP: 192.168.1.1\n"
            "- Multiple IPs: 192.168.1.1,192.168.1.5,192.168.1.10"
        )
    
    def validate_target_ports(self, value):
        """Validate port specification"""
        if not value:
            return value
        
        # Validate port format (e.g., "22,80,443,1000-2000")
        import re
        port_pattern = r'^(\d+(-\d+)?)(,\d+(-\d+)?)*$'
        
        if not re.match(port_pattern, value):
            raise serializers.ValidationError(
                "Invalid port format. Use comma-separated ports or ranges (e.g., '22,80,443,1000-2000')"
            )
        
        return value


class NetworkScanUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating scan configuration"""
    
    class Meta:
        model = NetworkScan
        fields = [
            'name', 'description', 'priority', 'exclude_hosts',
            'timing_template', 'max_retries', 'timeout_per_host',
            'max_parallel_hosts', 'max_parallel_ports', 'randomize_hosts',
            'service_detection', 'version_detection', 'os_detection',
            'script_scanning', 'aggressive_scan', 'is_scheduled',
            'schedule_cron', 'auto_retry_on_failure', 'max_auto_retries',
            'generate_report', 'report_format', 'tags', 'metadata'
        ]


class ScanTemplateSerializer(serializers.ModelSerializer):
    """Serializer for scan templates"""
    
    scan_type_display = serializers.CharField(source='get_scan_type_display', read_only=True)
    timing_template_display = serializers.CharField(source='get_timing_template_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ScanTemplate
        fields = [
            'id', 'name', 'description', 'scan_type', 'scan_type_display',
            'default_ports', 'scan_techniques', 'timing_template', 'timing_template_display',
            'service_detection', 'version_detection', 'os_detection', 'script_scanning',
            'max_parallel_hosts', 'timeout_per_host', 'is_builtin',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['is_builtin', 'created_by', 'created_at', 'updated_at']


class ScanTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating scan templates"""
    
    class Meta:
        model = ScanTemplate
        fields = [
            'name', 'description', 'scan_type', 'default_ports',
            'scan_techniques', 'timing_template', 'service_detection',
            'version_detection', 'os_detection', 'script_scanning',
            'max_parallel_hosts', 'timeout_per_host'
        ]


class ScanProgressSerializer(serializers.Serializer):
    """Serializer for scan progress updates"""
    
    scan_id = serializers.CharField()
    status = serializers.CharField()
    progress_percentage = serializers.IntegerField()
    current_phase = serializers.CharField()
    current_target = serializers.CharField()
    estimated_completion = serializers.DateTimeField()
    hosts_scanned = serializers.IntegerField()
    ports_scanned = serializers.IntegerField()
    scan_rate = serializers.FloatField()
    errors_count = serializers.IntegerField()
    warnings_count = serializers.IntegerField()


class ScanResultsSerializer(serializers.Serializer):
    """Serializer for detailed scan results"""
    
    scan_id = serializers.CharField()
    scan_type = serializers.CharField()
    target_range = serializers.CharField()
    status = serializers.CharField()
    duration = serializers.FloatField()
    
    # Summary statistics
    total_hosts_scanned = serializers.IntegerField()
    hosts_up = serializers.IntegerField()
    hosts_down = serializers.IntegerField()
    success_rate = serializers.FloatField()
    
    total_ports_scanned = serializers.IntegerField()
    open_ports_found = serializers.IntegerField()
    port_discovery_rate = serializers.FloatField()
    
    services_detected = serializers.IntegerField()
    vulnerabilities_found = serializers.IntegerField()
    risk_score = serializers.IntegerField()
    
    # Detailed results
    host_results = serializers.ListField()
    port_results = serializers.ListField()
    service_results = serializers.ListField()
    vulnerability_results = serializers.ListField()
    
    # Performance metrics
    scan_rate = serializers.FloatField()
    bandwidth_used = serializers.FloatField()
    cpu_usage_avg = serializers.FloatField()
    memory_usage_peak = serializers.FloatField()
    
    # Issues
    errors_count = serializers.IntegerField()
    warnings_count = serializers.IntegerField()
    error_log = serializers.CharField()


class NetworkTrafficSerializer(serializers.ModelSerializer):
    device_ip = serializers.CharField(source='device.ip_address', read_only=True)
    device_hostname = serializers.CharField(source='device.hostname', read_only=True)
    total_bytes = serializers.ReadOnlyField()
    total_packets = serializers.ReadOnlyField()
    
    class Meta:
        model = NetworkTraffic
        fields = [
            'id', 'device', 'device_ip', 'device_hostname', 'timestamp',
            'bytes_sent', 'bytes_received', 'packets_sent', 'packets_received',
            'active_connections', 'bandwidth_usage', 'total_bytes', 'total_packets'
        ]


class SecurityEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    source_device_ip = serializers.CharField(source='source_device.ip_address', read_only=True)
    target_device_ip = serializers.CharField(source='target_device.ip_address', read_only=True)
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_type', 'event_type_display', 'severity', 'severity_display',
            'source_device', 'source_device_ip', 'target_device', 'target_device_ip',
            'title', 'description', 'timestamp', 'details', 'is_resolved',
            'resolved_at', 'resolved_by', 'resolved_by_username'
        ]
        read_only_fields = ['timestamp', 'resolved_at', 'resolved_by']


class SecurityEventResolveSerializer(serializers.Serializer):
    """Serializer for resolving security events"""
    pass


class NetworkConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkConfiguration
        fields = [
            'id', 'name', 'description', 'auto_scan_enabled', 'scan_interval',
            'scan_range', 'traffic_monitoring', 'security_monitoring',
            'packet_capture', 'alert_on_new_devices', 'alert_on_device_offline',
            'alert_on_port_scan', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id', 'is_staff']


# Dashboard summary serializers
class DashboardStatsSerializer(serializers.Serializer):
    total_devices = serializers.IntegerField()
    online_devices = serializers.IntegerField()
    offline_devices = serializers.IntegerField()
    total_scans = serializers.IntegerField()
    active_scans = serializers.IntegerField()
    security_events_today = serializers.IntegerField()
    unresolved_events = serializers.IntegerField()


class NetworkOverviewSerializer(serializers.Serializer):
    network_range = serializers.CharField()
    total_ips = serializers.IntegerField()
    discovered_devices = serializers.IntegerField()
    device_types = serializers.DictField()
    last_scan = serializers.DateTimeField()


class TrafficSummarySerializer(serializers.Serializer):
    device_ip = serializers.CharField()
    hostname = serializers.CharField()
    total_bytes = serializers.IntegerField()
    bandwidth_usage = serializers.FloatField()
    last_updated = serializers.DateTimeField() 