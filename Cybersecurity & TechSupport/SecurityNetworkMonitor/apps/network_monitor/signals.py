from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import NetworkDevice, SecurityEvent, NetworkScan
import logging

logger = logging.getLogger('network_monitor')
channel_layer = get_channel_layer()


@receiver(post_save, sender=NetworkDevice)
def device_updated(sender, instance, created, **kwargs):
    """Handle device creation/update"""
    try:
        if channel_layer:
            # Broadcast device update via WebSocket
            async_to_sync(channel_layer.group_send)(
                "network_updates",
                {
                    "type": "device_update",
                    "device": {
                        "id": instance.id,
                        "ip_address": instance.ip_address,
                        "hostname": instance.hostname,
                        "device_type": instance.device_type,
                        "status": instance.status,
                        "last_seen": instance.last_seen.isoformat(),
                        "response_time": instance.response_time,
                        "is_monitored": instance.is_monitored,
                    },
                    "timestamp": timezone.now().isoformat()
                }
            )
            
            if created:
                logger.info(f"New device discovered: {instance.ip_address}")
            else:
                logger.debug(f"Device updated: {instance.ip_address}")
                
    except Exception as e:
        logger.error(f"Error broadcasting device update: {e}")


@receiver(post_save, sender=SecurityEvent)
def security_event_created(sender, instance, created, **kwargs):
    """Handle security event creation"""
    if created:
        try:
            if channel_layer:
                # Broadcast security event via WebSocket
                async_to_sync(channel_layer.group_send)(
                    "security_updates",
                    {
                        "type": "security_event",
                        "event_type": instance.event_type,
                        "severity": instance.severity,
                        "title": instance.title,
                        "description": instance.description,
                        "timestamp": instance.timestamp.isoformat()
                    }
                )
                
            logger.warning(f"Security event created: {instance.title} ({instance.severity})")
            
        except Exception as e:
            logger.error(f"Error broadcasting security event: {e}")


@receiver(post_save, sender=NetworkScan)
def scan_status_updated(sender, instance, created, **kwargs):
    """Handle scan status updates"""
    try:
        if channel_layer and not created:  # Only for updates, not creation
            # Broadcast scan update via WebSocket
            async_to_sync(channel_layer.group_send)(
                "network_updates",
                {
                    "type": "scan_update",
                    "scan_id": instance.scan_id,
                    "status": instance.status,
                    "hosts_up": instance.hosts_up,
                    "progress_percentage": instance.progress_percentage,
                    "timestamp": timezone.now().isoformat()
                }
            )
            
        logger.info(f"Scan {instance.scan_id} status: {instance.status}")
        
    except Exception as e:
        logger.error(f"Error broadcasting scan update: {e}") 