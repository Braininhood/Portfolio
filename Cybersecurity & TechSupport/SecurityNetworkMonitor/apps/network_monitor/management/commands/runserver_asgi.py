"""
Custom management command to run Django development server with ASGI support
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import sys


class Command(BaseCommand):
    help = 'Run the Django development server with ASGI support (WebSocket enabled)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port', '-p',
            type=int,
            default=8000,
            help='Port to run the server on (default: 8000)'
        )
        parser.add_argument(
            '--bind', '-b',
            default='127.0.0.1',
            help='Interface to bind to (default: 127.0.0.1)'
        )

    def handle(self, *args, **options):
        port = options['port']
        bind = options['bind']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting ASGI development server at http://{bind}:{port}/')
        )
        self.stdout.write(
            self.style.SUCCESS('WebSocket support enabled for real-time features')
        )
        self.stdout.write(
            self.style.WARNING('Quit the server with CTRL+C')
        )
        
        # Run Daphne with the ASGI application
        try:
            asgi_app = settings.ASGI_APPLICATION
            # Ensure the ASGI path has the correct format for Daphne
            if ':' not in asgi_app:
                asgi_app = asgi_app.replace('.application', ':application')
            
            cmd = [
                sys.executable, '-m', 'daphne',
                '-p', str(port),
                '-b', bind,
                asgi_app
            ]
            subprocess.run(cmd)
        except KeyboardInterrupt:
            self.stdout.write('\nShutting down server...')
        except Exception as e:
            self.stderr.write(f'Error starting server: {e}')
            self.stderr.write('Make sure daphne is installed: pip install daphne') 