import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from apps.network_monitor.models import NetworkDevice, SecurityEvent


class NetworkMonitorConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time network monitoring updates"""
    
    async def connect(self):
        # Temporarily disable authentication for testing
        # if self.scope["user"] == AnonymousUser():
        #     await self.close()
        #     return
        
        # Join network monitoring groups
        await self.channel_layer.group_add("network_monitor", self.channel_name)
        await self.channel_layer.group_add("network_updates", self.channel_name)
        await self.channel_layer.group_add("security_updates", self.channel_name)
        await self.channel_layer.group_add("traffic_updates", self.channel_name)
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        # Leave groups
        await self.channel_layer.group_discard("network_monitor", self.channel_name)
        await self.channel_layer.group_discard("network_updates", self.channel_name)
        await self.channel_layer.group_discard("security_updates", self.channel_name)
        await self.channel_layer.group_discard("traffic_updates", self.channel_name)
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'subscribe':
                # Handle subscription to specific updates
                channels = data.get('channels', [])
                for channel in channels:
                    await self.channel_layer.group_add(channel, self.channel_name)
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'channels': channels,
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'unsubscribe':
                # Handle unsubscription
                channels = data.get('channels', [])
                for channel in channels:
                    await self.channel_layer.group_discard(channel, self.channel_name)
                await self.send(text_data=json.dumps({
                    'type': 'unsubscribed',
                    'channels': channels,
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'get_devices':
                # Send current device list
                devices = await self.get_all_devices()
                await self.send(text_data=json.dumps({
                    'type': 'device_list',
                    'devices': devices,
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'heartbeat':
                # Keep connection alive
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_ack',
                    'timestamp': timezone.now().isoformat()
                }))
                    
        except json.JSONDecodeError as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Invalid JSON format: {str(e)}'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'WebSocket error: {str(e)}'
            }))
    
    async def send_initial_data(self):
        """Send initial data when client connects"""
        try:
            # Get all devices and recent stats
            devices = await self.get_all_devices()
            stats = await self.get_network_stats()
            
            await self.send(text_data=json.dumps({
                'type': 'initial_state',
                'devices': devices,
                'stats': stats,
                'timestamp': timezone.now().isoformat()
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to send initial data: {str(e)}'
            }))
    
    @database_sync_to_async
    def get_all_devices(self):
        """Get all network devices with current status"""
        devices = NetworkDevice.objects.all().order_by('-last_seen')
        return [
            {
                'id': device.id,
                'ip_address': device.ip_address,
                'hostname': device.hostname or 'Unknown',
                'mac_address': device.mac_address,
                'device_type': device.device_type,
                'manufacturer': device.manufacturer,
                'status': device.status,
                'last_seen': device.last_seen.isoformat(),
                'first_seen': device.first_seen.isoformat(),
                'response_time': device.response_time,
                'avg_response_time': device.avg_response_time,
                'uptime_percentage': device.uptime_percentage,
                'packet_loss_rate': device.packet_loss_rate,
                'open_ports': device.open_ports,
                'services_running': device.services_running,
                'security_score': device.security_score,
                'is_scanning': device.is_scanning,
                'scan_progress': device.scan_progress,
                'monitor_enabled': device.monitor_enabled,
                'current_bandwidth_usage': device.current_bandwidth_usage,
                'total_bytes_in': device.total_bytes_in,
                'total_bytes_out': device.total_bytes_out,
            }
            for device in devices
        ]
    
    @database_sync_to_async
    def get_network_stats(self):
        """Get network statistics"""
        total_devices = NetworkDevice.objects.count()
        online_devices = NetworkDevice.objects.filter(status='online').count()
        offline_devices = NetworkDevice.objects.filter(status='offline').count()
        unknown_devices = NetworkDevice.objects.filter(status='unknown').count()
        
        # Recent activity
        recent_devices = NetworkDevice.objects.filter(
            first_seen__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # Security events
        unresolved_alerts = SecurityEvent.objects.filter(is_resolved=False).count()
        critical_alerts = SecurityEvent.objects.filter(
            is_resolved=False, severity='critical'
        ).count()
        
        return {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': offline_devices,
            'unknown_devices': unknown_devices,
            'new_devices_today': recent_devices,
            'unresolved_alerts': unresolved_alerts,
            'critical_alerts': critical_alerts,
            'last_updated': timezone.now().isoformat()
        }

    # Enhanced message handlers for real-time events
    async def device_status_changed(self, event):
        """Handle device status changes"""
        await self.send(text_data=json.dumps({
            'type': 'device_status_changed',
            'device_id': event['device_id'],
            'ip_address': event['ip_address'],
            'hostname': event.get('hostname', ''),
            'old_status': event['old_status'],
            'new_status': event['new_status'],
            'response_time': event.get('response_time'),
            'last_seen': event['last_seen'],
            'timestamp': event['timestamp']
        }))
    
    async def device_discovered(self, event):
        """Handle new device discoveries"""
        await self.send(text_data=json.dumps({
            'type': 'device_discovered',
            'device': event['device'],
            'timestamp': event['timestamp']
        }))
    
    async def port_scan_started(self, event):
        """Handle port scan start"""
        await self.send(text_data=json.dumps({
            'type': 'port_scan_started',
            'device_id': event.get('device_id'),
            'device_ip': event.get('device_ip', event.get('ip_address')),  # Support both field names
            'status': event.get('status', 'scan_started'),
            'progress': event.get('progress', 0),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    async def port_scan_progress(self, event):
        """Handle port scan progress updates"""
        await self.send(text_data=json.dumps({
            'type': 'port_scan_progress',
            'device_id': event.get('device_id'),
            'device_ip': event.get('device_ip', event.get('ip_address')),  # Support both field names
            'progress': event.get('progress', 0),
            'status': event.get('status', 'scanning'),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    async def port_scan_complete(self, event):
        """Handle port scan completion"""
        await self.send(text_data=json.dumps({
            'type': 'port_scan_complete',
            'device_id': event['device_id'],
            'device_ip': event.get('device_ip', event.get('ip_address')),  # Support both field names
            'open_ports': event['open_ports'],
            'scan_time': event.get('scan_time'),
            'timestamp': event['timestamp']
        }))

    async def port_scan_error(self, event):
        """Handle port scan errors"""
        await self.send(text_data=json.dumps({
            'type': 'port_scan_error',
            'device_id': event.get('device_id'),
            'device_ip': event.get('device_ip', event.get('ip_address')),  # Support both field names
            'status': event.get('status', 'scan_failed'),
            'error': event.get('error', 'Unknown error'),
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))
    
    async def network_stats_update(self, event):
        """Handle network statistics updates"""
        await self.send(text_data=json.dumps({
            'type': 'network_stats_update',
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def security_alert(self, event):
        """Handle security alerts"""
        await self.send(text_data=json.dumps({
            'type': 'security_alert',
            'alert': {
                'event_type': event['event_type'],
                'severity': event['severity'],
                'title': event['title'],
                'description': event['description'],
                'source_device': event.get('source_device'),
                'target_device': event.get('target_device'),
            },
            'timestamp': event['timestamp']
        }))

    # Legacy message handlers (keeping for backward compatibility)
    async def device_update(self, event):
        """Handle device status updates (legacy)"""
        await self.send(text_data=json.dumps({
            'type': 'device_update',
            'device': event['device'],
            'timestamp': event['timestamp']
        }))
    
    async def scan_update(self, event):
        """Handle network scan updates"""
        await self.send(text_data=json.dumps({
            'type': 'scan_update',
            'scan_id': event['scan_id'],
            'status': event['status'],
            'hosts_up': event.get('hosts_up', 0),
            'progress_percentage': event.get('progress_percentage', 0),
            'timestamp': event['timestamp']
        }))
    
    async def scan_progress_update(self, event):
        """Handle detailed scan progress updates"""
        await self.send(text_data=json.dumps({
            'type': 'scan_progress_update',
            'scan_id': event['scan_id'],
            'status': event.get('status'),
            'progress_percentage': event.get('progress_percentage', 0),
            'current_phase': event.get('current_phase'),
            'current_target': event.get('current_target'),
            'hosts_scanned': event.get('hosts_scanned', 0),
            'hosts_up': event.get('hosts_up', 0),
            'open_ports_found': event.get('open_ports_found', 0),
            'services_detected': event.get('services_detected', 0),
            'vulnerabilities_found': event.get('vulnerabilities_found', 0),
            'risk_score': event.get('risk_score', 0),
            'timestamp': event['timestamp']
        }))
    
    async def scan_started(self, event):
        """Handle scan start notifications"""
        await self.send(text_data=json.dumps({
            'type': 'scan_started',
            'scan_id': event['scan_id'],
            'scan_type': event.get('scan_type'),
            'target_range': event.get('target_range'),
            'timestamp': event['timestamp']
        }))
    
    async def scan_completed(self, event):
        """Handle scan completion notifications"""
        await self.send(text_data=json.dumps({
            'type': 'scan_completed',
            'scan_id': event['scan_id'],
            'status': event.get('status'),
            'duration': event.get('duration'),
            'hosts_scanned': event.get('hosts_scanned', 0),
            'hosts_up': event.get('hosts_up', 0),
            'open_ports_found': event.get('open_ports_found', 0),
            'services_detected': event.get('services_detected', 0),
            'vulnerabilities_found': event.get('vulnerabilities_found', 0),
            'risk_score': event.get('risk_score', 0),
            'timestamp': event['timestamp']
        }))
    
    async def scan_failed(self, event):
        """Handle scan failure notifications"""
        await self.send(text_data=json.dumps({
            'type': 'scan_failed',
            'scan_id': event['scan_id'],
            'error': event.get('error'),
            'timestamp': event['timestamp']
        }))
    
    async def security_event(self, event):
        """Handle security event notifications"""
        # Handle both direct event data and nested event data
        event_data = event.get('event', event)
        await self.send(text_data=json.dumps({
            'type': 'security_event',
            'event_type': event_data.get('event_type', event.get('event_type')),
            'severity': event_data.get('severity', event.get('severity')),
            'title': event_data.get('title', event.get('title')),
            'description': event_data.get('description', event.get('description')),
            'timestamp': event_data.get('timestamp', event.get('timestamp'))
        }))
    
    async def traffic_update(self, event):
        """Handle traffic monitoring updates"""
        await self.send(text_data=json.dumps({
            'type': 'traffic_update',
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp', '')
        }))
    
    async def port_changes_detected(self, event):
        """Handle port changes detection"""
        await self.send(text_data=json.dumps({
            'type': 'port_changes_detected',
            'device_id': event['device_id'],
            'device_ip': event['device_ip'],
            'hostname': event.get('hostname', ''),
            'new_ports': event['new_ports'],
            'closed_ports': event['closed_ports'],
            'timestamp': event['timestamp']
        }))
    
    async def devices_cleared(self, event):
        """Handle devices cleared event"""
        await self.send(text_data=json.dumps({
            'type': 'devices_cleared',
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
    
    async def device_ip_changed(self, event):
        """Handle device IP change event"""
        await self.send(text_data=json.dumps({
            'type': 'device_ip_changed',
            'device_id': event['device_id'],
            'old_ip': event['old_ip'],
            'new_ip': event['new_ip'],
            'mac_address': event['mac_address'],
            'hostname': event.get('hostname', ''),
            'timestamp': event['timestamp']
        }))


class ScanProgressConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time scan progress updates"""
    
    async def connect(self):
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
        
        self.scan_id = self.scope['url_route']['kwargs']['scan_id']
        self.scan_group_name = f'scan_{self.scan_id}'
        
        # Join scan-specific group
        await self.channel_layer.group_add(
            self.scan_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave scan group
        await self.channel_layer.group_discard(
            self.scan_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'scan_id': self.scan_id
                }))
        except json.JSONDecodeError:
            pass
    
    async def scan_progress(self, event):
        """Handle scan progress updates"""
        await self.send(text_data=json.dumps({
            'type': 'scan_progress',
            'scan_id': event['scan_id'],
            'progress': event['progress'],
            'current_ip': event.get('current_ip'),
            'hosts_up': event.get('hosts_up', 0),
            'timestamp': event['timestamp']
        }))
    
    async def scan_complete(self, event):
        """Handle scan completion"""
        await self.send(text_data=json.dumps({
            'type': 'scan_complete',
            'scan_id': event['scan_id'],
            'status': event['status'],
            'hosts_up': event.get('hosts_up', 0),
            'duration': event.get('duration'),
            'timestamp': event['timestamp']
        }))


class DeviceDetailConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time device-specific updates"""
    
    async def connect(self):
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
        
        self.device_ip = self.scope['url_route']['kwargs']['device_ip']
        self.device_group_name = f'device_{self.device_ip.replace(".", "_")}'
        
        # Join device-specific group
        await self.channel_layer.group_add(
            self.device_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial device data
        await self.send_device_data()
    
    async def disconnect(self, close_code):
        # Leave device group
        await self.channel_layer.group_discard(
            self.device_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping_device':
                # Trigger a ping for this specific device
                await self.ping_device()
            elif message_type == 'scan_ports':
                # Trigger port scan for this device
                ports = data.get('ports')
                await self.scan_device_ports(ports)
                
        except json.JSONDecodeError:
            pass
    
    async def send_device_data(self):
        """Send current device data"""
        try:
            device_data = await self.get_device_data()
            if device_data:
                await self.send(text_data=json.dumps({
                    'type': 'device_data',
                    'device': device_data,
                    'timestamp': asyncio.get_event_loop().time()
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Failed to get device data: {str(e)}'
            }))
    
    @database_sync_to_async
    def get_device_data(self):
        """Get device data from database"""
        try:
            device = NetworkDevice.objects.get(ip_address=self.device_ip)
            return {
                'id': device.id,
                'ip_address': device.ip_address,
                'hostname': device.hostname,
                'mac_address': device.mac_address,
                'device_type': device.device_type,
                'status': device.status,
                'last_seen': device.last_seen.isoformat(),
                'response_time': device.response_time,
                'open_ports': device.open_ports,
                'is_monitored': device.is_monitored
            }
        except NetworkDevice.DoesNotExist:
            return None
    
    async def ping_device(self):
        """Trigger ping for this device"""
        # This would integrate with the network scanner
        # For now, just send a placeholder response
        await self.send(text_data=json.dumps({
            'type': 'ping_result',
            'device_ip': self.device_ip,
            'status': 'ping_started'
        }))
    
    async def scan_device_ports(self, ports):
        """Trigger port scan for this device"""
        try:
            # Import the real-time monitor
            from apps.network_monitor.services import RealTimeNetworkMonitor
            from apps.network_monitor.models import NetworkDevice
            
            # Get the device
            device = await database_sync_to_async(NetworkDevice.objects.get)(ip_address=self.device_ip)
            
            # Send scan started message
            await self.send(text_data=json.dumps({
                'type': 'port_scan_started',
                'device_ip': self.device_ip,
                'status': 'scan_started',
                'progress': 0
            }))
            
            # Create monitor instance and scan ports
            monitor = RealTimeNetworkMonitor()
            
            # Scan ports in background task
            asyncio.create_task(self.perform_port_scan(monitor, device, ports))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'port_scan_error',
                'device_ip': self.device_ip,
                'status': 'scan_failed',
                'error': str(e)
            }))
    
    async def perform_port_scan(self, monitor, device, ports):
        """Perform the actual port scan"""
        try:
            # Send progress updates
            await self.send(text_data=json.dumps({
                'type': 'port_scan_progress',
                'device_ip': self.device_ip,
                'progress': 25,
                'status': 'scanning'
            }))
            
            # Perform the scan
            await monitor.scan_device_ports(device)
            
            # Get updated device data
            updated_device = await database_sync_to_async(NetworkDevice.objects.get)(ip_address=self.device_ip)
            
            # Send completion message
            await self.send(text_data=json.dumps({
                'type': 'port_scan_complete',
                'device_ip': self.device_ip,
                'status': 'scan_complete',
                'progress': 100,
                'open_ports': updated_device.open_ports,
                'scan_time': updated_device.last_port_scan.isoformat() if updated_device.last_port_scan else None
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'port_scan_error',
                'device_ip': self.device_ip,
                'status': 'scan_failed',
                'error': str(e)
            }))
    
    # Message handlers
    async def device_status_update(self, event):
        """Handle device status updates"""
        if event['device_ip'] == self.device_ip:
            await self.send(text_data=json.dumps({
                'type': 'device_status_update',
                'device_ip': event['device_ip'],
                'status': event['status'],
                'response_time': event.get('response_time'),
                'timestamp': event['timestamp']
            }))
    
    async def device_traffic_update(self, event):
        """Handle device traffic updates"""
        if event['device_ip'] == self.device_ip:
            await self.send(text_data=json.dumps({
                'type': 'traffic_update',
                'device_ip': event['device_ip'],
                'traffic_data': event['traffic_data'],
                'timestamp': event['timestamp']
            }))
    
    async def port_scan_result(self, event):
        """Handle port scan results"""
        if event['device_ip'] == self.device_ip:
            await self.send(text_data=json.dumps({
                'type': 'port_scan_result',
                'device_ip': event['device_ip'],
                'open_ports': event['open_ports'],
                'timestamp': event['timestamp']
            })) 