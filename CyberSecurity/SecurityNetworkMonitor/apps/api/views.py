from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Avg, F
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import ipaddress
import asyncio
import uuid
import threading
import logging

from apps.network_monitor.models import (
    NetworkDevice, NetworkScan, NetworkTraffic, 
    SecurityEvent, NetworkInterface, NetworkConfiguration, ScanTemplate
)
# from apps.network_monitor.services import network_scanner, traffic_monitor  # Temporarily commented out
from .serializers import (
    NetworkDeviceSerializer, NetworkDeviceCreateSerializer,
    NetworkScanSerializer, NetworkScanCreateSerializer, NetworkScanUpdateSerializer,
    ScanTemplateSerializer, ScanTemplateCreateSerializer,
    NetworkTrafficSerializer, SecurityEventSerializer,
    SecurityEventResolveSerializer, NetworkInterfaceSerializer,
    NetworkConfigurationSerializer, DashboardStatsSerializer,
    NetworkOverviewSerializer, TrafficSummarySerializer
)

logger = logging.getLogger(__name__)

# Global monitoring state
_global_monitor = None
_global_monitor_thread = None
_monitoring_active = False
_monitoring_tasks = []  # Track asyncio tasks for proper cancellation


@method_decorator(csrf_exempt, name='dispatch')
class NetworkDeviceViewSet(viewsets.ModelViewSet):
    """Network device management"""
    queryset = NetworkDevice.objects.all()
    serializer_class = NetworkDeviceSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NetworkDeviceCreateSerializer
        return NetworkDeviceSerializer
    
    def get_queryset(self):
        queryset = NetworkDevice.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by device type
        device_type = self.request.query_params.get('device_type')
        if device_type:
            queryset = queryset.filter(device_type=device_type)
        
        # Filter by monitored status
        monitored = self.request.query_params.get('monitored')
        if monitored is not None:
            queryset = queryset.filter(is_monitored=monitored.lower() == 'true')
        
        # Search by IP or hostname
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(ip_address__icontains=search) | 
                Q(hostname__icontains=search)
            )
        
        return queryset.order_by('-last_seen')
    
    @action(detail=True, methods=['post'])
    def toggle_monitoring(self, request, pk=None):
        """Toggle device monitoring status"""
        device = self.get_object()
        device.is_monitored = not device.is_monitored
        device.save()
        
        return Response({
            'id': device.id,
            'is_monitored': device.is_monitored,
            'message': f"Monitoring {'enabled' if device.is_monitored else 'disabled'} for {device.ip_address}"
        })
    
    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """Clear all devices from the list"""
        try:
            # Get count before deletion
            device_count = NetworkDevice.objects.count()
            
            # Delete all devices
            NetworkDevice.objects.all().delete()
            
            # Also clear related data
            from apps.network_monitor.models import DeviceStatusHistory, SecurityEvent
            DeviceStatusHistory.objects.all().delete()
            SecurityEvent.objects.all().delete()
            
            # Broadcast clear event via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)('network_monitor', {
                    'type': 'devices_cleared',
                    'message': f'All {device_count} devices cleared',
                    'timestamp': timezone.now().isoformat()
                })
            
            logger.info(f"All {device_count} devices cleared from database")
            
            # Automatically start a quick discovery scan after clearing devices
            try:
                import threading
                import time
                from apps.network_monitor.services import NetworkScanner
                
                def delayed_discovery():
                    """Start discovery after a short delay"""
                    time.sleep(2)  # Wait 2 seconds for frontend to process clear event
                    try:
                        scanner = NetworkScanner()
                        logger.info("Starting automatic network discovery after device clear")
                        
                        # Start background discovery
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        async def run_discovery():
                            import uuid
                            network_range = "192.168.1.0/24"  # Default network range
                            scan_id = str(uuid.uuid4())
                            await scanner.discover_devices(network_range, scan_id)
                            logger.info("Automatic discovery completed after device clear")
                        
                        loop.run_until_complete(run_discovery())
                        loop.close()
                        
                    except Exception as e:
                        logger.error(f"Error in automatic discovery after clear: {e}")
                
                # Start discovery in background thread
                discovery_thread = threading.Thread(target=delayed_discovery, daemon=True)
                discovery_thread.start()
                
                logger.info("Automatic discovery scheduled after device clear")
                
            except Exception as e:
                logger.warning(f"Could not start automatic discovery: {e}")
            
            return Response({
                'success': True,
                'devices_cleared': device_count,
                'message': f'Successfully cleared {device_count} devices and started automatic discovery'
            })
            
        except Exception as e:
            logger.error(f"Error clearing devices: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Failed to clear devices'
            }, status=500)
    
    @action(detail=True, methods=['post'])
    def ping(self, request, pk=None):
        """Ping a specific device"""
        device = self.get_object()
        
        from apps.network_monitor.services import NetworkScanner
        scanner = NetworkScanner()
        is_alive, response_time = scanner.ping_host(device.ip_address)
        
        # Update device status
        device.status = 'online' if is_alive else 'offline'
        device.response_time = response_time if is_alive else None
        device.last_seen = timezone.now() if is_alive else device.last_seen
        device.save()
        
        return Response({
            'device_ip': device.ip_address,
            'is_alive': is_alive,
            'response_time': response_time,
            'status': device.status,
            'message': f"Ping {'successful' if is_alive else 'failed'}"
        })
    
    @action(detail=True, methods=['post'])
    def scan_ports(self, request, pk=None):
        """Scan ports on a specific device with real-time updates"""
        device = self.get_object()
        ports = request.data.get('ports', None)
        include_udp = request.data.get('include_udp', True)
        
        # Use the comprehensive scanning with WebSocket updates
        import asyncio
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        async def perform_comprehensive_scan():
            from apps.network_monitor.services import RealTimeNetworkMonitor
            monitor = RealTimeNetworkMonitor()
            
            # Send initial WebSocket notification to network monitor group
            channel_layer = get_channel_layer()
            
            if channel_layer:
                await channel_layer.group_send('network_monitor', {
                    'type': 'port_scan_started',
                    'device_id': device.id,
                    'device_ip': device.ip_address,
                    'ip_address': device.ip_address,  # Support both field names
                    'status': 'scan_started',
                    'progress': 0,
                    'timestamp': timezone.now().isoformat()
                })
            
            # Perform the comprehensive scan
            try:
                open_ports = await monitor.scan_device_ports(device)
                return open_ports
            except Exception as e:
                # Send error notification to network monitor group
                if channel_layer:
                    await channel_layer.group_send('network_monitor', {
                        'type': 'port_scan_error',
                        'device_id': device.id,
                        'device_ip': device.ip_address,
                        'ip_address': device.ip_address,  # Support both field names
                        'status': 'scan_failed',
                        'error': str(e),
                        'timestamp': timezone.now().isoformat()
                    })
                raise e
        
        try:
            # Run the async scan
            open_ports = async_to_sync(perform_comprehensive_scan)()
            
            # Refresh device data
            device.refresh_from_db()
            
            # Count ports by risk level for summary
            risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            for port in device.open_ports:
                risk_level = port.get('risk_level', 'medium')
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            
            return Response({
                'device_ip': device.ip_address,
                'open_ports': device.open_ports,
                'total_open_ports': len(device.open_ports),
                'risk_summary': risk_counts,
                'scan_includes_udp': include_udp,
                'scan_completed': True,
                'scan_time': device.last_port_scan.isoformat() if device.last_port_scan else None,
                'message': f"Comprehensive scan found {len(device.open_ports)} open ports ({risk_counts['critical']} critical, {risk_counts['high']} high risk)"
            })
            
        except Exception as e:
            return Response({
                'error': f"Port scan failed: {str(e)}",
                'device_ip': device.ip_address,
                'scan_completed': False
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NetworkScanViewSet(viewsets.ModelViewSet):
    """Advanced network scan management with comprehensive features"""
    queryset = NetworkScan.objects.all()
    serializer_class = NetworkScanSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    filterset_fields = ['status', 'scan_type', 'priority', 'started_by']
    search_fields = ['name', 'description', 'target_range']
    ordering_fields = ['started_at', 'completed_at', 'priority', 'progress_percentage']
    ordering = ['-started_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NetworkScanCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NetworkScanUpdateSerializer
        return NetworkScanSerializer
    
    def get_queryset(self):
        queryset = NetworkScan.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by scan type
        scan_type = self.request.query_params.get('scan_type')
        if scan_type:
            queryset = queryset.filter(scan_type=scan_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(started_at__gte=start_date)
            except ValueError:
                pass
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(started_at__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Create and optionally start a new network scan"""
        import uuid
        
        # Handle anonymous users
        user = self.request.user if self.request.user.is_authenticated else None
        
        # Generate unique scan ID
        scan_id = str(uuid.uuid4())
        
        # Save the scan
        scan = serializer.save(
            started_by=user,
            scan_id=scan_id,
            status='pending'
        )
        
        # Auto-start if requested
        auto_start = self.request.data.get('auto_start', False)
        if auto_start:
            self._start_scan_execution(scan)
    
    def _start_scan_execution(self, scan):
        """Start the actual scan execution"""
        try:
            from apps.network_monitor.scan_engine import scan_engine
            
            # Prepare scan configuration
            scan_config = {
                'scan_id': scan.scan_id,
                'scan_type': scan.scan_type,
                'target_range': scan.target_range,
                'target_ports': scan.target_ports,
                'exclude_hosts': scan.exclude_hosts,
                'scan_techniques': scan.scan_techniques,
                'timing_template': scan.timing_template,
                'service_detection': scan.service_detection,
                'version_detection': scan.version_detection,
                'os_detection': scan.os_detection,
                'script_scanning': scan.script_scanning,
                'aggressive_scan': scan.aggressive_scan,
                'max_parallel_hosts': scan.max_parallel_hosts,
                'timeout_per_host': scan.timeout_per_host,
            }
            
            # Start scan in background thread
            def run_scan():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(scan_engine.execute_scan(scan_config))
                except Exception as e:
                    logger.error(f"Scan execution failed: {e}")
                    scan.mark_failed(str(e))
                finally:
                    loop.close()
            
            scan_thread = threading.Thread(target=run_scan)
            scan_thread.daemon = True
            scan_thread.start()
            
            # Update scan status
            scan.status = 'initializing'
            scan.save()
            
            logger.info(f"Started scan execution for {scan.scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to start scan execution: {e}")
            scan.mark_failed(str(e))
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a pending scan"""
        scan = self.get_object()
        
        if scan.status != 'pending':
            return Response(
                {'error': f'Cannot start scan in {scan.status} status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self._start_scan_execution(scan)
        
        return Response({
            'message': 'Scan started successfully',
            'scan_id': scan.scan_id,
            'status': scan.status
        })
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a running scan"""
        scan = self.get_object()
        
        if scan.status != 'running':
            return Response(
                {'error': 'Can only pause running scans'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scan.pause()
        
        return Response({
            'message': 'Scan paused successfully',
            'scan_id': scan.scan_id,
            'status': scan.status
        })
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused scan"""
        scan = self.get_object()
        
        if scan.status != 'paused':
            return Response(
                {'error': 'Can only resume paused scans'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scan.resume()
        
        return Response({
            'message': 'Scan resumed successfully',
            'scan_id': scan.scan_id,
            'status': scan.status
        })
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop a running or paused scan"""
        scan = self.get_object()
        
        if scan.status not in ['running', 'paused']:
            return Response(
                {'error': 'Can only stop running or paused scans'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scan.cancel()
        
        return Response({
            'message': 'Scan stopped successfully',
            'scan_id': scan.scan_id,
            'status': scan.status
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scan"""
        scan = self.get_object()
        
        if scan.status in ['completed', 'failed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel scan in {scan.status} status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scan.cancel()
        
        return Response({
            'message': 'Scan cancelled successfully',
            'scan_id': scan.scan_id,
            'status': scan.status
        })
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get scan progress information"""
        scan = self.get_object()
        
        progress_data = {
            'scan_id': scan.scan_id,
            'status': scan.status,
            'progress_percentage': scan.progress_percentage,
            'current_phase': scan.current_phase,
            'current_target': scan.current_target,
            'estimated_completion': scan.estimated_completion,
            'hosts_scanned': scan.total_hosts_scanned,
            'ports_scanned': scan.total_ports_scanned,
            'scan_rate': scan.scan_rate,
            'errors_count': scan.errors_count,
            'warnings_count': scan.warnings_count,
            'duration': scan.duration,
            'estimated_time_remaining': scan.estimated_time_remaining,
        }
        
        return Response(progress_data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get detailed scan results"""
        scan = self.get_object()
        
        if scan.status not in ['completed', 'failed', 'cancelled']:
            return Response(
                {'error': 'Scan results not available yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results_data = {
            'scan_id': scan.scan_id,
            'scan_type': scan.scan_type,
            'target_range': scan.target_range,
            'status': scan.status,
            'duration': scan.duration,
            'summary': scan.get_scan_summary(),
            'host_results': scan.host_results,
            'port_results': scan.port_results,
            'service_results': scan.service_results,
            'vulnerability_results': scan.vulnerability_results,
            'performance_metrics': {
                'scan_rate': scan.scan_rate,
                'bandwidth_used': scan.bandwidth_used,
                'cpu_usage_avg': scan.cpu_usage_avg,
                'memory_usage_peak': scan.memory_usage_peak,
            },
            'issues': {
                'errors_count': scan.errors_count,
                'warnings_count': scan.warnings_count,
                'error_log': scan.error_log,
            }
        }
        
        return Response(results_data)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """Download scan report in various formats"""
        scan = self.get_object()
        
        # Debug logging
        logger.info(f"Report request for scan {pk}, query params: {request.query_params}")
        
        if scan.status not in ['completed', 'failed', 'cancelled']:
            return Response(
                {'error': 'Scan report not available yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report_format = request.query_params.get('format', 'txt')
        logger.info(f"Report format requested: {report_format}")
        
        if report_format == 'txt' or report_format is None:
            from django.http import HttpResponse
            
            # Create human-readable text report
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("NETWORK SECURITY SCAN REPORT")
            report_lines.append("=" * 80)
            report_lines.append("")
            
            # Scan Information
            report_lines.append("SCAN INFORMATION:")
            report_lines.append("-" * 40)
            report_lines.append(f"Scan ID: {scan.scan_id}")
            report_lines.append(f"Name: {scan.name}")
            report_lines.append(f"Description: {scan.description}")
            report_lines.append(f"Scan Type: {scan.get_scan_type_display()}")
            report_lines.append(f"Target Range: {scan.target_range}")
            report_lines.append(f"Target Ports: {scan.target_ports}")
            report_lines.append(f"Status: {scan.get_status_display()}")
            report_lines.append(f"Started: {scan.started_at.strftime('%Y-%m-%d %H:%M:%S') if scan.started_at else 'N/A'}")
            report_lines.append(f"Completed: {scan.completed_at.strftime('%Y-%m-%d %H:%M:%S') if scan.completed_at else 'N/A'}")
            report_lines.append(f"Duration: {scan.duration}")
            report_lines.append(f"Progress: {scan.progress_percentage}%")
            report_lines.append("")
            
            # Statistics
            report_lines.append("SCAN STATISTICS:")
            report_lines.append("-" * 40)
            report_lines.append(f"Total Hosts Scanned: {scan.total_hosts_scanned}")
            report_lines.append(f"Hosts Up: {scan.hosts_up}")
            report_lines.append(f"Hosts Down: {scan.hosts_down}")
            report_lines.append(f"Total Ports Scanned: {scan.total_ports_scanned}")
            report_lines.append(f"Open Ports Found: {scan.open_ports_found}")
            report_lines.append(f"Services Detected: {scan.services_detected}")
            report_lines.append(f"Vulnerabilities Found: {scan.vulnerabilities_found}")
            report_lines.append(f"Risk Score: {scan.risk_score}")
            report_lines.append(f"Scan Rate: {scan.scan_rate} packets/sec")
            report_lines.append(f"Bandwidth Used: {scan.bandwidth_used} MB")
            report_lines.append("")
            
            # Results Summary
            summary = scan.get_scan_summary()
            if summary:
                report_lines.append("RESULTS SUMMARY:")
                report_lines.append("-" * 40)
                for key, value in summary.items():
                    report_lines.append(f"{key.replace('_', ' ').title()}: {value}")
                report_lines.append("")
            
            # Host Results
            if scan.host_results:
                report_lines.append("HOST RESULTS:")
                report_lines.append("-" * 40)
                for i, host in enumerate(scan.host_results, 1):
                    if isinstance(host, dict):
                        report_lines.append(f"{i}. Host: {host.get('ip', 'Unknown')}")
                        report_lines.append(f"   Status: {host.get('status', 'Unknown')}")
                        report_lines.append(f"   Response Time: {host.get('response_time', 'N/A')} ms")
                        if host.get('hostname'):
                            report_lines.append(f"   Hostname: {host.get('hostname')}")
                        if host.get('mac_address'):
                            report_lines.append(f"   MAC Address: {host.get('mac_address')}")
                        report_lines.append("")
            
            # Port Results
            if scan.port_results:
                report_lines.append("PORT SCAN RESULTS:")
                report_lines.append("-" * 40)
                for i, port in enumerate(scan.port_results, 1):
                    if isinstance(port, dict):
                        report_lines.append(f"{i}. Port: {port.get('port', 'Unknown')}")
                        report_lines.append(f"   Protocol: {port.get('protocol', 'TCP')}")
                        report_lines.append(f"   State: {port.get('state', 'Unknown')}")
                        if port.get('service'):
                            report_lines.append(f"   Service: {port.get('service')}")
                        if port.get('version'):
                            report_lines.append(f"   Version: {port.get('version')}")
                        report_lines.append("")
            
            # Service Results
            if scan.service_results:
                report_lines.append("SERVICE DETECTION RESULTS:")
                report_lines.append("-" * 40)
                for i, service in enumerate(scan.service_results, 1):
                    if isinstance(service, dict):
                        report_lines.append(f"{i}. Service: {service.get('name', 'Unknown')}")
                        report_lines.append(f"   Port: {service.get('port', 'Unknown')}")
                        report_lines.append(f"   Version: {service.get('version', 'Unknown')}")
                        if service.get('banner'):
                            report_lines.append(f"   Banner: {service.get('banner')}")
                        report_lines.append("")
            
            # Vulnerability Results
            if scan.vulnerability_results:
                report_lines.append("VULNERABILITY SCAN RESULTS:")
                report_lines.append("-" * 40)
                for i, vuln in enumerate(scan.vulnerability_results, 1):
                    if isinstance(vuln, dict):
                        report_lines.append(f"{i}. Vulnerability: {vuln.get('name', 'Unknown')}")
                        report_lines.append(f"   Severity: {vuln.get('severity', 'Unknown')}")
                        report_lines.append(f"   Description: {vuln.get('description', 'N/A')}")
                        if vuln.get('solution'):
                            report_lines.append(f"   Solution: {vuln.get('solution')}")
                        report_lines.append("")
            
            # Footer
            report_lines.append("=" * 80)
            report_lines.append(f"Report Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("Generated by: Network Security Monitor v1.0")
            report_lines.append("=" * 80)
            
            # Create text response
            report_text = "\n".join(report_lines)
            
            response = HttpResponse(
                report_text,
                content_type='text/plain; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename="scan_report_{scan.scan_id[:8]}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
                }
            )
            
            return response
        
        elif report_format == 'json':
            import json
            from django.http import HttpResponse
            
            # Get comprehensive scan data
            report_data = {
                'scan_info': {
                    'scan_id': scan.scan_id,
                    'name': scan.name,
                    'description': scan.description,
                    'scan_type': scan.scan_type,
                    'target_range': scan.target_range,
                    'target_ports': scan.target_ports,
                    'status': scan.status,
                    'started_at': scan.started_at.isoformat() if scan.started_at else None,
                    'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
                    'duration': scan.duration,
                    'progress_percentage': scan.progress_percentage,
                },
                'results_summary': scan.get_scan_summary(),
                'detailed_results': {
                    'host_results': scan.host_results or [],
                    'port_results': scan.port_results or [],
                    'service_results': scan.service_results or [],
                    'vulnerability_results': scan.vulnerability_results or [],
                },
                'statistics': {
                    'total_hosts_scanned': scan.total_hosts_scanned,
                    'hosts_up': scan.hosts_up,
                    'hosts_down': scan.hosts_down,
                    'total_ports_scanned': scan.total_ports_scanned,
                    'open_ports_found': scan.open_ports_found,
                    'services_detected': scan.services_detected,
                    'vulnerabilities_found': scan.vulnerabilities_found,
                    'risk_score': scan.risk_score,
                    'scan_rate': scan.scan_rate,
                    'bandwidth_used': scan.bandwidth_used,
                },
                'metadata': {
                    'report_generated_at': timezone.now().isoformat(),
                    'report_format': 'json',
                    'generator': 'Network Security Monitor v1.0'
                }
            }
            
            # Create JSON response
            json_data = json.dumps(report_data, indent=2, ensure_ascii=False)
            
            response = HttpResponse(
                json_data,
                content_type='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename="scan_report_{scan.scan_id[:8]}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
                }
            )
            
            return response
        
        # TODO: Implement other formats (PDF, CSV, XML)
        return Response(
            {'error': f'Report format {report_format} not supported yet'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get scan statistics"""
        stats = {
            'total_scans': NetworkScan.objects.count(),
            'scans_by_status': {
                status_choice[0]: NetworkScan.objects.filter(status=status_choice[0]).count()
                for status_choice in NetworkScan.STATUS_CHOICES
            },
            'scans_by_type': {
                type_choice[0]: NetworkScan.objects.filter(scan_type=type_choice[0]).count()
                for type_choice in NetworkScan.SCAN_TYPES
            },
            'scans_by_priority': {
                priority_choice[0]: NetworkScan.objects.filter(priority=priority_choice[0]).count()
                for priority_choice in NetworkScan.PRIORITY_CHOICES
            },
            'recent_scans': NetworkScan.objects.filter(
                started_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'avg_scan_duration': NetworkScan.objects.filter(
                status='completed'
            ).aggregate(
                avg_duration=Avg(
                    F('completed_at') - F('started_at')
                )
            )['avg_duration'],
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get scan history with filtering"""
        queryset = self.get_queryset()
        
        # Additional filtering for history
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            since_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(started_at__gte=since_date)
        except ValueError:
            pass
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def quick_discovery(self, request):
        """Start a quick network discovery scan"""
        target_range = request.data.get('target_range', '192.168.1.0/24')
        
        # Create scan
        scan_data = {
            'name': f'Quick Discovery - {target_range}',
            'description': 'Quick network discovery scan',
            'scan_type': 'discovery',
            'priority': 'normal',
            'target_range': target_range,
            'timing_template': 'aggressive',
            'service_detection': False,
            'version_detection': False,
            'os_detection': False,
        }
        
        serializer = NetworkScanCreateSerializer(data=scan_data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            scan = serializer.save(
                started_by=user,
                scan_id=str(uuid.uuid4()),
                status='pending'
            )
            
            # Auto-start the scan
            self._start_scan_execution(scan)
            
            return Response(NetworkScanSerializer(scan).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def quick_port_scan(self, request):
        """Start a quick port scan"""
        target_range = request.data.get('target_range')
        target_ports = request.data.get('target_ports', '22,80,443,8080')
        
        if not target_range:
            return Response(
                {'error': 'target_range is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create scan
        scan_data = {
            'name': f'Quick Port Scan - {target_range}',
            'description': f'Quick port scan for ports: {target_ports}',
            'scan_type': 'port_scan',
            'priority': 'normal',
            'target_range': target_range,
            'target_ports': target_ports,
            'timing_template': 'aggressive',
            'service_detection': True,
            'version_detection': False,
            'os_detection': False,
        }
        
        serializer = NetworkScanCreateSerializer(data=scan_data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            scan = serializer.save(
                started_by=user,
                scan_id=str(uuid.uuid4()),
                status='pending'
            )
            
            # Auto-start the scan
            self._start_scan_execution(scan)
            
            return Response(NetworkScanSerializer(scan).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def quick_vulnerability_scan(self, request):
        """Start a quick vulnerability scan"""
        target_range = request.data.get('target_range')
        
        if not target_range:
            return Response(
                {'error': 'target_range is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create scan
        scan_data = {
            'name': f'Quick Vulnerability Scan - {target_range}',
            'description': 'Quick vulnerability assessment scan',
            'scan_type': 'vulnerability_scan',
            'priority': 'high',
            'target_range': target_range,
            'timing_template': 'normal',
            'service_detection': True,
            'version_detection': True,
            'os_detection': True,
            'script_scanning': True,
        }
        
        serializer = NetworkScanCreateSerializer(data=scan_data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            scan = serializer.save(
                started_by=user,
                scan_id=str(uuid.uuid4()),
                status='pending'
            )
            
            # Auto-start the scan
            self._start_scan_execution(scan)
            
            return Response(NetworkScanSerializer(scan).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class ScanTemplateViewSet(viewsets.ModelViewSet):
    """Scan template management"""
    queryset = ScanTemplate.objects.all()
    serializer_class = ScanTemplateSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScanTemplateCreateSerializer
        return ScanTemplateSerializer
    
    def perform_create(self, serializer):
        """Create a new scan template"""
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)
    
    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of built-in templates"""
        template = self.get_object()
        if template.is_builtin:
            return Response(
                {'error': 'Cannot delete built-in templates'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def create_scan(self, request, pk=None):
        """Create a new scan based on this template"""
        template = self.get_object()
        
        # Get target range from request
        target_range = request.data.get('target_range')
        if not target_range:
            return Response(
                {'error': 'target_range is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get any overrides from request
        overrides = request.data.get('overrides', {})
        
        # Create scan from template
        user = request.user if request.user.is_authenticated else None
        scan = template.create_scan(target_range, user, **overrides)
        
        # Auto-start if requested
        auto_start = request.data.get('auto_start', False)
        if auto_start:
            # Use the scan viewset method to start execution
            scan_viewset = NetworkScanViewSet()
            scan_viewset._start_scan_execution(scan)
        
        serializer = NetworkScanSerializer(scan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class NetworkTrafficViewSet(viewsets.ReadOnlyModelViewSet):
    """Network traffic monitoring"""
    queryset = NetworkTraffic.objects.all()
    serializer_class = NetworkTrafficSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    
    def get_queryset(self):
        queryset = NetworkTraffic.objects.all()
        
        # Filter by device
        device_id = self.request.query_params.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filter by time range
        since = self.request.query_params.get('since')
        if since:
            try:
                since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=since_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get traffic summary for all devices"""
        devices = NetworkDevice.objects.filter(status='online', is_monitored=True)
        summaries = []
        
        for device in devices:
            latest_traffic = device.traffic.first()
            if latest_traffic:
                summaries.append({
                    'device_ip': device.ip_address,
                    'hostname': device.hostname,
                    'total_bytes': latest_traffic.total_bytes,
                    'bandwidth_usage': latest_traffic.bandwidth_usage,
                    'last_updated': latest_traffic.timestamp
                })
        
        serializer = TrafficSummarySerializer(summaries, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class SecurityEventViewSet(viewsets.ModelViewSet):
    """Security event management"""
    queryset = SecurityEvent.objects.all()
    serializer_class = SecurityEventSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    
    def get_queryset(self):
        queryset = SecurityEvent.objects.all()
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by resolved status
        resolved = self.request.query_params.get('resolved')
        if resolved is not None:
            queryset = queryset.filter(is_resolved=resolved.lower() == 'true')
        
        return queryset.order_by('-timestamp')
    
    @action(detail=True, methods=['post'])
    def investigate(self, request, pk=None):
        """Mark a security event as under investigation"""
        event = self.get_object()
        
        if event.is_resolved:
            return Response(
                {'error': 'Event already resolved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add investigation details to the event
        if not event.details:
            event.details = {}
        
        event.details['investigated_at'] = timezone.now().isoformat()
        event.details['investigated_by'] = request.user.username if request.user.is_authenticated else 'anonymous'
        event.details['status'] = 'under_investigation'
        event.save()
        
        serializer = self.get_serializer(event)
        return Response({
            'message': 'Event marked as under investigation',
            'event': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a security event"""
        try:
            event = self.get_object()
            
            if event.is_resolved:
                return Response(
                    {'error': 'Event already resolved'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Pass user only if authenticated, otherwise None
            user = request.user if request.user.is_authenticated else None
            event.resolve(user)
            
            serializer = self.get_serializer(event)
            return Response({
                'message': 'Security event resolved successfully',
                'event': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error resolving security event {pk}: {str(e)}")
            return Response(
                {'error': f'Failed to resolve event: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a security threat"""
        try:
            event = self.get_object()
            
            # Add blocking details to the event
            if not event.details:
                event.details = {}
            
            event.details['blocked_at'] = timezone.now().isoformat()
            event.details['blocked_by'] = request.user.username if request.user.is_authenticated else 'anonymous'
            event.details['status'] = 'blocked'
            event.details['action_taken'] = 'threat_blocked'
            event.save()
            
            # Auto-resolve blocked events
            if not event.is_resolved:
                user = request.user if request.user.is_authenticated else None
                event.resolve(user)
            
            serializer = self.get_serializer(event)
            return Response({
                'message': 'Security threat blocked successfully',
                'event': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error blocking security event {pk}: {str(e)}")
            return Response(
                {'error': f'Failed to block threat: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get security event statistics"""
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get severity counts for unresolved events
        severity_counts = SecurityEvent.objects.filter(is_resolved=False).values('severity').annotate(count=Count('id'))
        severity_dict = {item['severity']: item['count'] for item in severity_counts}
        
        stats = {
            'total_events': SecurityEvent.objects.count(),
            'events_today': SecurityEvent.objects.filter(timestamp__gte=today).count(),
            'unresolved_events': SecurityEvent.objects.filter(is_resolved=False).count(),
            'critical_events': severity_dict.get('critical', 0),
            'high_events': severity_dict.get('high', 0),
            'medium_events': severity_dict.get('medium', 0),
            'low_events': severity_dict.get('low', 0),
            'events_by_severity': dict(
                SecurityEvent.objects.values('severity').annotate(
                    count=Count('id')
                ).values_list('severity', 'count')
            ),
            'events_by_type': dict(
                SecurityEvent.objects.values('event_type').annotate(
                    count=Count('id')
                ).values_list('event_type', 'count')
            )
        }
        
        return Response(stats)

    @action(detail=False, methods=['get'])
    def all(self, request):
        """Get all security events without pagination for dashboard"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class NetworkInterfaceViewSet(viewsets.ReadOnlyModelViewSet):
    """Network interface information"""
    queryset = NetworkInterface.objects.all()
    serializer_class = NetworkInterfaceSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    
    @action(detail=False, methods=['get'])
    def discover(self, request):
        """Discover available network interfaces"""
        # interfaces = network_scanner.get_network_interfaces()
        
        # # Update database with discovered interfaces
        # for iface_data in interfaces:
        #     NetworkInterface.objects.update_or_create(
        #         name=iface_data['name'],
        #         ip_address=iface_data['ip'],
        #         defaults={
        #             'mac_address': iface_data.get('mac', ''),
        #             'is_active': True
        #         }
        #     )
        
        # Return updated list
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class NetworkConfigurationViewSet(viewsets.ModelViewSet):
    """Network configuration management"""
    queryset = NetworkConfiguration.objects.all()
    serializer_class = NetworkConfigurationSerializer
    permission_classes = [AllowAny]  # Temporarily allow all for testing
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a configuration"""
        config = self.get_object()
        config.activate()
        
        # # Start/stop monitoring based on configuration
        # if config.traffic_monitoring:
        #     traffic_monitor.start_monitoring()
        # else:
        #     traffic_monitor.stop_monitoring()
        
        serializer = self.get_serializer(config)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow all for testing
def dashboard_stats(request):
    """Get dashboard statistics"""
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = {
        'total_devices': NetworkDevice.objects.count(),
        'online_devices': NetworkDevice.objects.filter(status='online').count(),
        'offline_devices': NetworkDevice.objects.filter(status='offline').count(),
        'total_scans': NetworkScan.objects.count(),
        'active_scans': NetworkScan.objects.filter(status='running').count(),
        'security_events_today': SecurityEvent.objects.filter(timestamp__gte=today).count(),
        'unresolved_events': SecurityEvent.objects.filter(is_resolved=False).count()
    }
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow all for testing
def network_overview(request):
    """Get network overview information"""
    # Get active configuration or use defaults
    try:
        config = NetworkConfiguration.objects.get(is_active=True)
        network_range = config.scan_range
    except NetworkConfiguration.DoesNotExist:
        # network_range = network_scanner.auto_detect_network_range()
        network_range = "192.168.1.0/24"  # Default fallback
    
    try:
        network = ipaddress.IPv4Network(network_range, strict=False)
        total_ips = network.num_addresses - 2  # Exclude network and broadcast
    except:
        total_ips = 0
    
    # Get device type distribution
    device_types = dict(
        NetworkDevice.objects.values('device_type').annotate(
            count=Count('id')
        ).values_list('device_type', 'count')
    )
    
    # Get last scan
    last_scan = NetworkScan.objects.filter(
        status='completed'
    ).order_by('-completed_at').first()
    
    overview = {
        'network_range': network_range,
        'total_ips': total_ips,
        'discovered_devices': NetworkDevice.objects.count(),
        'device_types': device_types,
        'last_scan': last_scan.completed_at if last_scan else None
    }
    
    serializer = NetworkOverviewSerializer(overview)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow all for testing
@csrf_exempt
def start_monitoring(request):
    """Start comprehensive network monitoring (devices + traffic)"""
    global _global_monitor, _global_monitor_thread, _monitoring_active, _monitoring_tasks
    
    try:
        from apps.network_monitor import services
        RealTimeNetworkMonitor = services.RealTimeNetworkMonitor
        from apps.network_monitor.monitoring_services.traffic_monitor import get_traffic_monitor
        
        # Check if already running
        if _monitoring_active and _global_monitor_thread and _global_monitor_thread.is_alive():
            return Response({
                'message': 'Network monitoring is already running',
                'status': 'active',
                'monitoring_interval': '5 seconds',
                'features': ['device_status_tracking', 'traffic_monitoring', 'real_time_updates', 'threat_detection']
            })
        
        # Clean up any previous monitoring state
        _monitoring_tasks.clear()
        
        # Get or create the global monitor instances
        if _global_monitor is None:
            _global_monitor = RealTimeNetworkMonitor()
        
        traffic_monitor = get_traffic_monitor()
        
        # Set monitoring as active
        _monitoring_active = True
        
        # Start both device and traffic monitoring
        import asyncio
        import threading
        
        def start_async_monitoring():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def run_both_monitors():
                try:
                    # Create tasks for both monitors
                    device_task = asyncio.create_task(_global_monitor.start_monitoring())
                    traffic_task = asyncio.create_task(traffic_monitor.start_monitoring())
                    
                    # Store tasks for cancellation
                    _monitoring_tasks.extend([device_task, traffic_task])
                    
                    # Wait for both monitors to complete
                    await asyncio.gather(device_task, traffic_task, return_exceptions=True)
                except asyncio.CancelledError:
                    logger.info("Monitoring tasks cancelled successfully")
                except Exception as e:
                    logger.error(f"Error in monitoring tasks: {e}")
                finally:
                    # Clean up
                    global _monitoring_active
                    _monitoring_active = False
                    _monitoring_tasks.clear()
            
            try:
                loop.run_until_complete(run_both_monitors())
            except Exception as e:
                logger.error(f"Error in monitoring event loop: {e}")
            finally:
                loop.close()
        
        # Start in background thread
        _global_monitor_thread = threading.Thread(target=start_async_monitoring, daemon=True)
        _global_monitor_thread.start()
        
        logger.info("Comprehensive network monitoring started successfully")
        
        return Response({
            'message': 'Comprehensive network monitoring started',
            'status': 'active',
            'monitoring_interval': '5 seconds',
            'features': ['device_status_tracking', 'traffic_monitoring', 'real_time_updates', 'threat_detection'],
            'monitors': ['device_monitor', 'traffic_monitor']
        })
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return Response({
            'message': f'Failed to start monitoring: {str(e)}',
            'status': 'error'
        }, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow all for testing
@csrf_exempt
def stop_monitoring(request):
    """Stop comprehensive network monitoring (devices + traffic)"""
    global _global_monitor, _global_monitor_thread, _monitoring_active, _monitoring_tasks
    
    try:
        from apps.network_monitor.monitoring_services.traffic_monitor import get_traffic_monitor
        
        logger.info("Stopping comprehensive network monitoring...")
        
        # Set monitoring as inactive first
        _monitoring_active = False
        
        # Stop monitor instances
        if _global_monitor:
            _global_monitor.is_scanning = False
            
        traffic_monitor = get_traffic_monitor()
        if traffic_monitor:
            traffic_monitor.is_monitoring = False
        
        # Cancel all running asyncio tasks
        if _monitoring_tasks:
            def cancel_monitoring_tasks():
                try:
                    # Don't create a new event loop, try to use the existing one
                    try:
                        loop = asyncio.get_running_loop()
                        # If we're in a running loop, schedule the cancellation
                        async def cancel_all_tasks():
                            # Cancel all monitoring tasks
                            for task in _monitoring_tasks:
                                if not task.done():
                                    task.cancel()
                            
                            # Wait for cancellation to complete
                            if _monitoring_tasks:
                                await asyncio.gather(*_monitoring_tasks, return_exceptions=True)
                        
                        # Schedule the cancellation in the existing loop
                        asyncio.create_task(cancel_all_tasks())
                        
                    except RuntimeError:
                        # No running loop, create a new one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        async def cancel_all_tasks():
                            # Cancel all monitoring tasks
                            for task in _monitoring_tasks:
                                if not task.done():
                                    task.cancel()
                            
                            # Wait for cancellation to complete
                            if _monitoring_tasks:
                                await asyncio.gather(*_monitoring_tasks, return_exceptions=True)
                        
                        loop.run_until_complete(cancel_all_tasks())
                        loop.close()
                        
                except Exception as e:
                    logger.warning(f"Task cancellation completed with minor issues: {e}")
                finally:
                    _monitoring_tasks.clear()
            
            # Cancel tasks in background thread
            cancel_thread = threading.Thread(target=cancel_monitoring_tasks, daemon=True)
            cancel_thread.start()
            cancel_thread.join(timeout=3)  # Wait up to 3 seconds
        
        # Wait for monitoring thread to finish
        if _global_monitor_thread and _global_monitor_thread.is_alive():
            _global_monitor_thread.join(timeout=5)
        
        # Reset global state
        _global_monitor = None
        _global_monitor_thread = None
        _monitoring_tasks.clear()
        
        logger.info("Comprehensive network monitoring stopped successfully")
        
        return Response({
            'message': 'Comprehensive network monitoring stopped', 
            'status': 'inactive',
            'monitors_stopped': ['device_monitor', 'traffic_monitor']
        })
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return Response({
            'message': f'Failed to stop monitoring: {str(e)}',
            'status': 'error'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow all for testing
def monitoring_status(request):
    """Get current monitoring status"""
    global _global_monitor, _global_monitor_thread, _monitoring_active
    
    try:
        # Check if monitoring is active
        is_active = _monitoring_active and _global_monitor_thread and _global_monitor_thread.is_alive()
        
        # Additional check for monitor state
        monitor_scanning = False
        if _global_monitor:
            monitor_scanning = getattr(_global_monitor, 'is_scanning', False)
        
        return Response({
            'status': 'active' if is_active and monitor_scanning else 'inactive',
            'message': 'Monitoring is currently active' if is_active and monitor_scanning else 'Monitoring is currently inactive',
            'thread_alive': _global_monitor_thread.is_alive() if _global_monitor_thread else False,
            'monitor_scanning': monitor_scanning,
            'global_active': _monitoring_active
        })
    except Exception as e:
        logger.error(f"Error checking monitoring status: {e}")
        return Response({
            'status': 'unknown',
            'message': f'Failed to check monitoring status: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])  # Temporarily allow all for testing
def real_time_traffic_metrics(request):
    """Get real-time traffic metrics including accurate packets per second"""
    try:
        from apps.network_monitor.monitoring_services.traffic_monitor import get_traffic_monitor
        
        traffic_monitor = get_traffic_monitor()
        
        # Get current network stats
        current_stats = traffic_monitor._get_network_stats()
        
        # Calculate metrics if we have previous data
        if traffic_monitor.last_network_stats:
            metrics = traffic_monitor._calculate_real_time_metrics(
                current_stats, 
                traffic_monitor.last_network_stats
            )
        else:
            # First call, return baseline
            metrics = {
                'bandwidth_mbps': 0.0,
                'bandwidth_utilization_percent': 0.0,
                'packets_per_second': 0,
                'bytes_per_second': 0,
                'active_connections': current_stats.get('active_connections', 0),
                'total_connections': current_stats.get('total_connections', 0),
                'error_rate': 0,
                'drop_rate': 0
            }
        
        # Update last stats for next calculation
        traffic_monitor.last_network_stats = current_stats
        
        return Response({
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'metrics': metrics,
            'monitoring_active': traffic_monitor.is_monitoring
        })
        
    except Exception as e:
        logger.error(f"Error getting real-time traffic metrics: {e}")
        return Response({
            'status': 'error',
            'message': str(e),
            'metrics': {
                'bandwidth_mbps': 0.0,
                'bandwidth_utilization_percent': 0.0,
                'packets_per_second': 0,
                'bytes_per_second': 0,
                'active_connections': 0,
                'total_connections': 0,
                'error_rate': 0,
                'drop_rate': 0
            }
        }, status=500)