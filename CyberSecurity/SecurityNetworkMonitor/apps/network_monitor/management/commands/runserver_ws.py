"""
Custom management command to run Django development server with WebSocket support
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys
import os


class Command(BaseCommand):
    help = 'Start Django development server with WebSocket support (ASGI)'

    def add_arguments(self, parser):
        parser.add_argument(
            'addrport', nargs='?',
            help='Optional port number, or ipaddr:port'
        )
        parser.add_argument(
            '--ipv6', '-6', action='store_true', dest='use_ipv6',
            help='Tells Django to use an IPv6 address.',
        )
        parser.add_argument(
            '--noreload', action='store_false', dest='use_reloader',
            help='Tells Django to NOT use the auto-reloader.',
        )

    def handle(self, *args, **options):
        # Import re module at the top of the method
        import re
        
        # Parse address and port
        if options['addrport']:
            m = re.match(r'^(?P<addr>.*):(?P<port>\d+)$', options['addrport'])
            if m:
                addr, port = m.groups()
            else:
                addr = ''
                port = options['addrport']
        else:
            addr = ''
            port = '8000'

        if not addr:
            addr = '127.0.0.1' if not options['use_ipv6'] else '::1'

        # Convert port to integer
        try:
            port = int(port)
        except ValueError:
            self.stderr.write(f"Error: {port!r} is not a valid port number.")
            return

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting ASGI development server at http://{addr}:{port}/')
        )
        self.stdout.write(
            self.style.SUCCESS('✅ WebSocket support: ENABLED')
        )
        self.stdout.write(
            self.style.SUCCESS('🔄 Real-time updates: ACTIVE')
        )
        self.stdout.write(
            self.style.WARNING('⏹️  Quit the server with CTRL+C')
        )
        self.stdout.write('')
        
        # Run Daphne with the ASGI application
        try:
            asgi_app = getattr(settings, 'ASGI_APPLICATION', 'network_monitor.asgi:application')
            # Ensure the ASGI path has the correct format for Daphne
            if ':' not in asgi_app:
                asgi_app = asgi_app.replace('.application', ':application')
            
            cmd = [
                sys.executable, '-m', 'daphne',
                '-p', str(port),
                '-b', addr,
                asgi_app
            ]
            
            # Set environment for development
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = 'network_monitor.settings'
            
            subprocess.run(cmd, env=env)
            
        except KeyboardInterrupt:
            self.stdout.write('\n' + self.style.SUCCESS('✅ Server stopped successfully.'))
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR('❌ Error: daphne not found. Install it with: pip install daphne')
            )
        except Exception as e:
            self.stderr.write(f'❌ Error starting ASGI server: {e}')
            self.stderr.write('💡 Tip: Use "python manage.py runserver" for basic HTTP-only server') 