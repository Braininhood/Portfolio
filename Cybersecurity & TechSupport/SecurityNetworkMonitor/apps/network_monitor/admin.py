from django.contrib import admin
from .models import (
    NetworkInterface, NetworkDevice, NetworkScan, ScanTemplate,
    NetworkTraffic, SecurityEvent, NetworkConfiguration
)


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'mac_address', 'is_active', 'created_at']
    list_filter = ['is_active', 'interface_type']
    search_fields = ['name', 'ip_address', 'mac_address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'hostname', 'device_type', 'status', 'last_seen', 'is_monitored']
    list_filter = ['device_type', 'status', 'is_monitored', 'first_seen']
    search_fields = ['ip_address', 'hostname', 'mac_address', 'manufacturer']
    readonly_fields = ['first_seen', 'created_at', 'updated_at']
    actions = ['enable_monitoring', 'disable_monitoring']
    
    def enable_monitoring(self, request, queryset):
        queryset.update(is_monitored=True)
        self.message_user(request, f"Enabled monitoring for {queryset.count()} devices.")
    enable_monitoring.short_description = "Enable monitoring for selected devices"
    
    def disable_monitoring(self, request, queryset):
        queryset.update(is_monitored=False)
        self.message_user(request, f"Disabled monitoring for {queryset.count()} devices.")
    disable_monitoring.short_description = "Disable monitoring for selected devices"


@admin.register(NetworkScan)
class NetworkScanAdmin(admin.ModelAdmin):
    list_display = ['scan_id', 'name', 'scan_type', 'target_range', 'status', 'priority', 'progress_percentage', 'started_at']
    list_filter = ['scan_type', 'status', 'priority', 'timing_template', 'started_at']
    search_fields = ['scan_id', 'name', 'target_range', 'description']
    readonly_fields = [
        'scan_id', 'started_at', 'completed_at', 'paused_at', 'progress_percentage',
        'current_phase', 'current_target', 'estimated_completion',
        'total_hosts_scanned', 'hosts_up', 'hosts_down', 'total_ports_scanned',
        'open_ports_found', 'services_detected', 'vulnerabilities_found',
        'scan_rate', 'bandwidth_used', 'cpu_usage_avg', 'memory_usage_peak',
        'errors_count', 'warnings_count', 'retry_count', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('scan_id', 'name', 'description', 'scan_type', 'priority', 'started_by')
        }),
        ('Target Configuration', {
            'fields': ('target_range', 'target_ports', 'exclude_hosts')
        }),
        ('Scan Configuration', {
            'fields': ('scan_techniques', 'timing_template', 'max_retries', 'timeout_per_host',
                      'max_parallel_hosts', 'max_parallel_ports', 'randomize_hosts')
        }),
        ('Detection Options', {
            'fields': ('service_detection', 'version_detection', 'os_detection', 
                      'script_scanning', 'aggressive_scan')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_percentage', 'current_phase', 'current_target',
                      'started_at', 'completed_at', 'paused_at', 'estimated_completion')
        }),
        ('Results', {
            'fields': ('total_hosts_scanned', 'hosts_up', 'hosts_down', 'total_ports_scanned',
                      'open_ports_found', 'services_detected', 'vulnerabilities_found')
        }),
        ('Performance', {
            'fields': ('scan_rate', 'bandwidth_used', 'cpu_usage_avg', 'memory_usage_peak')
        }),
        ('Issues', {
            'fields': ('errors_count', 'warnings_count', 'error_log')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_cron', 'next_run', 'auto_retry_on_failure',
                      'max_auto_retries', 'retry_count')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'created_at', 'updated_at')
        })
    )
    actions = ['cancel_scans', 'retry_failed_scans']
    
    def cancel_scans(self, request, queryset):
        cancelled_count = 0
        for scan in queryset:
            if scan.status in ['pending', 'running', 'paused']:
                scan.cancel()
                cancelled_count += 1
        self.message_user(request, f"Cancelled {cancelled_count} scans.")
    cancel_scans.short_description = "Cancel selected scans"
    
    def retry_failed_scans(self, request, queryset):
        retried_count = 0
        for scan in queryset:
            if scan.status == 'failed' and scan.retry_count < scan.max_auto_retries:
                scan.status = 'pending'
                scan.retry_count += 1
                scan.save()
                retried_count += 1
        self.message_user(request, f"Retried {retried_count} failed scans.")
    retry_failed_scans.short_description = "Retry failed scans"


@admin.register(ScanTemplate)
class ScanTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'scan_type', 'timing_template', 'is_builtin', 'created_by', 'created_at']
    list_filter = ['scan_type', 'timing_template', 'is_builtin', 'service_detection', 'version_detection']
    search_fields = ['name', 'description']
    readonly_fields = ['is_builtin', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'scan_type', 'created_by', 'is_builtin')
        }),
        ('Configuration', {
            'fields': ('default_ports', 'scan_techniques', 'timing_template')
        }),
        ('Detection Options', {
            'fields': ('service_detection', 'version_detection', 'os_detection', 'script_scanning')
        }),
        ('Performance', {
            'fields': ('max_parallel_hosts', 'timeout_per_host')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(NetworkTraffic)
class NetworkTrafficAdmin(admin.ModelAdmin):
    list_display = ['device', 'timestamp', 'bytes_sent', 'bytes_received', 'bandwidth_usage']
    list_filter = ['timestamp', 'device']
    search_fields = ['device__ip_address', 'device__hostname']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'severity', 'source_device', 'target_device', 'timestamp', 'is_resolved']
    list_filter = ['event_type', 'severity', 'is_resolved', 'timestamp']
    search_fields = ['title', 'description', 'source_device__ip_address', 'target_device__ip_address']
    readonly_fields = ['timestamp', 'resolved_at']
    actions = ['mark_resolved', 'mark_unresolved']
    
    def mark_resolved(self, request, queryset):
        for event in queryset:
            if not event.is_resolved:
                event.resolve(request.user)
        self.message_user(request, f"Marked {queryset.count()} events as resolved.")
    mark_resolved.short_description = "Mark selected events as resolved"
    
    def mark_unresolved(self, request, queryset):
        queryset.update(is_resolved=False, resolved_at=None, resolved_by=None)
        self.message_user(request, f"Marked {queryset.count()} events as unresolved.")
    mark_unresolved.short_description = "Mark selected events as unresolved"


@admin.register(NetworkConfiguration)
class NetworkConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'scan_range', 'auto_scan_enabled', 'is_active', 'created_at']
    list_filter = ['auto_scan_enabled', 'traffic_monitoring', 'security_monitoring', 'is_active']
    search_fields = ['name', 'description', 'scan_range']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_configuration']
    
    def activate_configuration(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "You can only activate one configuration at a time.", level='error')
            return
        
        config = queryset.first()
        config.activate()
        self.message_user(request, f"Activated configuration: {config.name}")
    activate_configuration.short_description = "Activate selected configuration" 