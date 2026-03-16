"""
Django management command to create sample data for Week 3: Basic Booking Flow.
Creates services, staff, staff areas, and sample appointments for testing.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.services.models import Category, Service
from apps.staff.models import Staff, StaffSchedule, StaffService, StaffArea
from apps.appointments.models import Appointment
from apps.customers.models import Customer
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create sample data for Week 3: Basic Booking Flow testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing sample data before creating new data',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        
        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing sample data...'))
            # Clear sample data (be careful in production!)
            Appointment.objects.filter(status__in=['pending', 'confirmed']).delete()
            StaffArea.objects.all().delete()
            StaffService.objects.all().delete()
            StaffSchedule.objects.all().delete()
            Staff.objects.filter(email__icontains='test').delete()
            Service.objects.filter(name__icontains='Test').delete()
            Category.objects.filter(name__icontains='Test').delete()
            self.stdout.write(self.style.SUCCESS('Sample data cleared!'))

        self.stdout.write(self.style.SUCCESS('\n=== Creating Week 3 Sample Data ===\n'))

        # 1. Create Categories
        self.stdout.write('Creating categories...')
        category_cleaning, _ = Category.objects.get_or_create(
            name='Cleaning Services',
            defaults={
                'description': 'Professional cleaning services for homes and businesses',
                'position': 1,
                'is_active': True,
            }
        )
        category_maintenance, _ = Category.objects.get_or_create(
            name='Maintenance Services',
            defaults={
                'description': 'Property maintenance and repair services',
                'position': 2,
                'is_active': True,
            }
        )
        category_green, _ = Category.objects.get_or_create(
            name='Green Spaces',
            defaults={
                'description': 'Garden and outdoor space maintenance',
                'position': 3,
                'is_active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'  [OK] Created categories'))

        # 2. Create Services
        self.stdout.write('Creating services...')
        services_data = [
            {
                'category': category_cleaning,
                'name': 'Window Cleaning',
                'description': 'Professional window cleaning service for residential and commercial properties',
                'duration': 60,
                'price': Decimal('35.00'),
                'currency': 'GBP',
                'position': 1,
            },
            {
                'category': category_cleaning,
                'name': 'Gutter Cleaning',
                'description': 'Thorough gutter cleaning and maintenance',
                'duration': 90,
                'price': Decimal('50.00'),
                'currency': 'GBP',
                'position': 2,
            },
            {
                'category': category_cleaning,
                'name': 'Pressure Washing',
                'description': 'High-pressure cleaning for driveways, patios, and exterior surfaces',
                'duration': 120,
                'price': Decimal('80.00'),
                'currency': 'GBP',
                'position': 3,
            },
            {
                'category': category_green,
                'name': 'Grass Cutting',
                'description': 'Regular lawn mowing and grass cutting service',
                'duration': 45,
                'price': Decimal('25.00'),
                'currency': 'GBP',
                'position': 1,
            },
            {
                'category': category_green,
                'name': 'Hedge Trimming',
                'description': 'Professional hedge trimming and shaping',
                'duration': 60,
                'price': Decimal('40.00'),
                'currency': 'GBP',
                'position': 2,
            },
            {
                'category': category_maintenance,
                'name': 'Gutter Repair',
                'description': 'Gutter repair and maintenance service',
                'duration': 120,
                'price': Decimal('100.00'),
                'currency': 'GBP',
                'position': 1,
            },
        ]

        services = []
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            services.append(service)
            if created:
                self.stdout.write(f'  [OK] Created service: {service.name}')
            else:
                self.stdout.write(f'  - Service already exists: {service.name}')

        # 3. Create Staff Members
        self.stdout.write('\nCreating staff members...')
        staff_data = [
            {
                'name': 'John Smith',
                'email': 'john.smith@multibook.test',
                'phone': '020 7123 4567',
                'bio': 'Experienced window cleaner with 5+ years in the industry',
                'is_active': True,
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@multibook.test',
                'phone': '07700 900123',
                'bio': 'Specialist in garden maintenance and green spaces',
                'is_active': True,
            },
            {
                'name': 'Mike Davis',
                'email': 'mike.davis@multibook.test',
                'phone': '020 7987 6543',
                'bio': 'Professional maintenance specialist',
                'is_active': True,
            },
        ]

        staff_members = []
        for staff_info in staff_data:
            staff, created = Staff.objects.get_or_create(
                email=staff_info['email'],
                defaults=staff_info
            )
            staff_members.append(staff)
            if created:
                self.stdout.write(f'  [OK] Created staff: {staff.name}')
            else:
                self.stdout.write(f'  - Staff already exists: {staff.name}')

        # 4. Assign Services to Staff
        self.stdout.write('\nAssigning services to staff...')
        # John - Window and Gutter Cleaning
        for service in [services[0], services[1], services[2]]:  # Window, Gutter Cleaning, Pressure Washing
            StaffService.objects.get_or_create(
                staff=staff_members[0],
                service=service,
                defaults={'is_active': True}
            )
            self.stdout.write(f'  [OK] Assigned {service.name} to {staff_members[0].name}')

        # Sarah - Green Spaces
        for service in [services[3], services[4]]:  # Grass Cutting, Hedge Trimming
            StaffService.objects.get_or_create(
                staff=staff_members[1],
                service=service,
                defaults={'is_active': True}
            )
            self.stdout.write(f'  [OK] Assigned {service.name} to {staff_members[1].name}')

        # Mike - Maintenance
        StaffService.objects.get_or_create(
            staff=staff_members[2],
            service=services[5],  # Gutter Repair
            defaults={'is_active': True}
        )
        self.stdout.write(f'  [OK] Assigned {services[5].name} to {staff_members[2].name}')

        # 5. Create Staff Schedules (Monday-Friday, 9am-5pm)
        self.stdout.write('\nCreating staff schedules...')
        for staff in staff_members:
            for day in range(5):  # Monday (0) to Friday (4)
                schedule, created = StaffSchedule.objects.get_or_create(
                    staff=staff,
                    day_of_week=day,
                    defaults={
                        'start_time': '09:00',
                        'end_time': '17:00',
                        'breaks': [{"start": "12:00", "end": "13:00"}],  # 1-hour lunch break
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(f'  [OK] Created schedule for {staff.name} - {schedule.get_day_of_week_display()}')

        # 6. Create Staff Service Areas (UK postcodes with radius)
        self.stdout.write('\nCreating staff service areas...')
        areas_data = [
            {
                'staff': staff_members[0],  # John
                'postcode': 'SW1A 1AA',  # Central London
                'radius_miles': Decimal('9.32'),  # ~15 km converted to miles
            },
            {
                'staff': staff_members[0],
                'postcode': 'W1A 0AX',  # West End
                'radius_miles': Decimal('6.21'),  # ~10 km converted to miles
            },
            {
                'staff': staff_members[1],  # Sarah
                'postcode': 'SW1A 1AA',  # Central London
                'radius_miles': Decimal('12.43'),  # ~20 km converted to miles
            },
            {
                'staff': staff_members[1],
                'postcode': 'N1 9GU',  # North London
                'radius_miles': Decimal('9.32'),  # ~15 km converted to miles
            },
            {
                'staff': staff_members[2],  # Mike
                'postcode': 'SW1A 1AA',  # Central London
                'radius_miles': Decimal('15.53'),  # ~25 km converted to miles
            },
            {
                'staff': staff_members[2],
                'postcode': 'E1 6AN',  # East London
                'radius_miles': Decimal('12.43'),  # ~20 km converted to miles
            },
        ]

        for area_data in areas_data:
            area, created = StaffArea.objects.get_or_create(
                staff=area_data['staff'],
                postcode=area_data['postcode'],
                defaults={
                    'radius_miles': area_data['radius_miles'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  [OK] Created service area: {area.staff.name} - {area.postcode} ({area.radius_miles} miles)')

        # 7. Create Sample Appointments (for next week)
        self.stdout.write('\nCreating sample appointments...')
        now = timezone.now()
        # Get next Monday at 10am
        days_until_monday = (7 - now.weekday()) % 7 or 7
        next_monday = (now + timedelta(days=days_until_monday)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        appointments_data = [
            {
                'staff': staff_members[0],
                'service': services[0],  # Window Cleaning
                'start_time': next_monday,
                'end_time': next_monday + timedelta(minutes=60),
                'status': 'confirmed',
            },
            {
                'staff': staff_members[1],
                'service': services[3],  # Grass Cutting
                'start_time': next_monday + timedelta(days=1, hours=14),
                'end_time': next_monday + timedelta(days=1, hours=14, minutes=45),
                'status': 'confirmed',
            },
            {
                'staff': staff_members[0],
                'service': services[1],  # Gutter Cleaning
                'start_time': next_monday + timedelta(days=2, hours=11),
                'end_time': next_monday + timedelta(days=2, hours=12, minutes=30),
                'status': 'pending',
            },
        ]

        for appt_data in appointments_data:
            appointment, created = Appointment.objects.get_or_create(
                staff=appt_data['staff'],
                service=appt_data['service'],
                start_time=appt_data['start_time'],
                defaults={
                    'end_time': appt_data['end_time'],
                    'status': appt_data['status'],
                }
            )
            if created:
                self.stdout.write(f'  [OK] Created appointment: {appointment.service.name} on {appointment.start_time.strftime("%Y-%m-%d %H:%M")}')

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(f'  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Services: {Service.objects.count()}')
        self.stdout.write(f'  Staff: {Staff.objects.count()}')
        self.stdout.write(f'  Staff Schedules: {StaffSchedule.objects.count()}')
        self.stdout.write(f'  Staff Service Areas: {StaffArea.objects.count()}')
        self.stdout.write(f'  Staff Services: {StaffService.objects.count()}')
        self.stdout.write(f'  Appointments: {Appointment.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Week 3 sample data created successfully!'))
        self.stdout.write('\nTest Postcodes:')
        self.stdout.write('  - SW1A 1AA (Westminster, London)')
        self.stdout.write('  - W1A 0AX (West End, London)')
        self.stdout.write('  - N1 9GU (Islington, London)')
        self.stdout.write('  - E1 6AN (Whitechapel, London)')
