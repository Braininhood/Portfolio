from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class NetworkMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.network_monitor'
    verbose_name = 'Network Monitor'

    def ready(self):
        import apps.network_monitor.signals
        
        # Only start monitoring for the main Django process (not during migrations, tests, etc.)
        import sys
        import os
        
        # Check if this is a management command that shouldn't start monitoring
        skip_monitoring_commands = [
            'makemigrations', 'migrate', 'test', 'check', 'collectstatic',
            'shell', 'dbshell', 'dumpdata', 'loaddata', 'createsuperuser',
            'changepassword', 'clearsessions', 'compilemessages', 'makemessages'
        ]
        
        # Check if we're running a management command
        is_management_command = len(sys.argv) > 1 and sys.argv[1] in skip_monitoring_commands
        
        # Check if we're in testing mode
        is_testing = 'test' in sys.argv or os.environ.get('TESTING') == 'True'
        
        # Automatic monitoring disabled - use manual start/stop controls instead
        logger.info("Real-time network monitoring is disabled on startup - use API endpoints to control monitoring")
        
        # # Only start monitoring for the main server process
        # if not is_management_command and not is_testing:
        #     try:
        #         from .services import realtime_monitor
        #         import asyncio
        #         import threading
        #         
        #         def start_realtime_monitoring():
        #             """Start the real-time monitoring in a separate thread"""
        #             try:
        #                 loop = asyncio.new_event_loop()
        #                 asyncio.set_event_loop(loop)
        #                 loop.run_until_complete(realtime_monitor.start_monitoring())
        #             except Exception as e:
        #                 logger.error(f"Error in real-time monitoring loop: {e}")
        #         
        #         # Start real-time monitoring in background thread
        #         monitoring_thread = threading.Thread(target=start_realtime_monitoring, daemon=True)
        #         monitoring_thread.start()
        #         
        #         logger.info("Real-time network monitoring started automatically")
        #     except Exception as e:
        #         logger.error(f"Failed to start real-time monitoring: {e}")
        # else:
        #     logger.debug(f"Skipping real-time monitoring startup (command: {sys.argv[1] if len(sys.argv) > 1 else 'unknown'})") 