"""
Management command to create default scan templates
"""

from django.core.management.base import BaseCommand
from apps.network_monitor.models import ScanTemplate


class Command(BaseCommand):
    help = 'Create default scan templates for network scanning'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Quick Discovery',
                'description': 'Fast network discovery scan to identify active hosts',
                'scan_type': 'ping_sweep',
                'default_ports': '',
                'scan_techniques': ['tcp_connect'],
                'timing_template': 'aggressive',
                'service_detection': False,
                'version_detection': False,
                'os_detection': False,
                'script_scanning': False,
                'max_parallel_hosts': 100,
                'timeout_per_host': 5,
                'is_builtin': True,
            },
            {
                'name': 'Basic Port Scan',
                'description': 'Standard port scan for common services',
                'scan_type': 'port_scan',
                'default_ports': '21,22,23,25,53,80,110,135,139,143,443,445,993,995,1433,3306,3389,5432,8080',
                'scan_techniques': ['tcp_connect'],
                'timing_template': 'normal',
                'service_detection': True,
                'version_detection': False,
                'os_detection': False,
                'script_scanning': False,
                'max_parallel_hosts': 50,
                'timeout_per_host': 10,
                'is_builtin': True,
            },
            {
                'name': 'Comprehensive Scan',
                'description': 'Thorough scan with service detection and OS fingerprinting',
                'scan_type': 'comprehensive',
                'default_ports': '1-1000',
                'scan_techniques': ['tcp_connect', 'udp'],
                'timing_template': 'normal',
                'service_detection': True,
                'version_detection': True,
                'os_detection': True,
                'script_scanning': False,
                'max_parallel_hosts': 25,
                'timeout_per_host': 30,
                'is_builtin': True,
            },
            {
                'name': 'Stealth Scan',
                'description': 'Low-profile scan to avoid detection',
                'scan_type': 'stealth_scan',
                'default_ports': '22,80,443',
                'scan_techniques': ['tcp_syn'],
                'timing_template': 'sneaky',
                'service_detection': True,
                'version_detection': False,
                'os_detection': False,
                'script_scanning': False,
                'max_parallel_hosts': 10,
                'timeout_per_host': 60,
                'is_builtin': True,
            },
            {
                'name': 'Vulnerability Assessment',
                'description': 'Security-focused scan with vulnerability detection',
                'scan_type': 'vulnerability_scan',
                'default_ports': '21,22,23,25,53,80,110,135,139,143,443,445,993,995,1433,3306,3389,5432,8080',
                'scan_techniques': ['tcp_connect'],
                'timing_template': 'normal',
                'service_detection': True,
                'version_detection': True,
                'os_detection': True,
                'script_scanning': True,
                'max_parallel_hosts': 20,
                'timeout_per_host': 45,
                'is_builtin': True,
            },
            {
                'name': 'Web Services Scan',
                'description': 'Focused scan for web servers and applications',
                'scan_type': 'service_detection',
                'default_ports': '80,443,8000,8080,8443,8888,9000,9080,9443',
                'scan_techniques': ['tcp_connect'],
                'timing_template': 'aggressive',
                'service_detection': True,
                'version_detection': True,
                'os_detection': False,
                'script_scanning': True,
                'max_parallel_hosts': 50,
                'timeout_per_host': 15,
                'is_builtin': True,
            },
            {
                'name': 'Database Services',
                'description': 'Scan for database servers and services',
                'scan_type': 'service_detection',
                'default_ports': '1433,1521,3306,5432,6379,27017,9042,7000,7001',
                'scan_techniques': ['tcp_connect'],
                'timing_template': 'normal',
                'service_detection': True,
                'version_detection': True,
                'os_detection': False,
                'script_scanning': True,
                'max_parallel_hosts': 30,
                'timeout_per_host': 20,
                'is_builtin': True,
            },
            {
                'name': 'IoT Device Discovery',
                'description': 'Scan for IoT and smart home devices',
                'scan_type': 'discovery',
                'default_ports': '80,443,1900,5000,5001,8081,8082,9080,1883,8883,5683',
                'scan_techniques': ['tcp_connect', 'udp'],
                'timing_template': 'polite',
                'service_detection': True,
                'version_detection': True,
                'os_detection': False,
                'script_scanning': False,
                'max_parallel_hosts': 40,
                'timeout_per_host': 25,
                'is_builtin': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = ScanTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            else:
                # Update existing template if it's built-in
                if template.is_builtin:
                    for key, value in template_data.items():
                        if key != 'name':  # Don't update the name
                            setattr(template, key, value)
                    template.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated template: {template.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Skipped custom template: {template.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nScan templates setup complete!\n'
                f'Created: {created_count} templates\n'
                f'Updated: {updated_count} templates'
            )
        ) 