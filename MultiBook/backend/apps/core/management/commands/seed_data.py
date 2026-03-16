"""
Seed simple data for local/Supabase: admin, customer, staff users + Week 3 sample data
(categories, services, staff members, schedules, areas, sample appointments).
Safe to run multiple times (get_or_create). Use after migrate on a fresh DB.
"""
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from apps.accounts.models import Manager
from apps.customers.models import Customer as CustomerModel
from apps.staff.models import Staff

User = get_user_model()

# Default passwords for seed users (change in production via env)
DEFAULT_ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', 'ChangeMe123!')
DEFAULT_CUSTOMER_PASSWORD = os.environ.get('SEED_CUSTOMER_PASSWORD', 'ChangeMe123!')
DEFAULT_STAFF_PASSWORD = os.environ.get('SEED_STAFF_PASSWORD', 'ChangeMe123!')
DEFAULT_MANAGER_PASSWORD = os.environ.get('SEED_MANAGER_PASSWORD', 'ChangeMe123!')


class Command(BaseCommand):
    help = 'Seed simple data: admin, customer, staff, manager users + categories, services, staff, appointments (Week 3 sample).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-sample',
            action='store_true',
            help='Only create users (admin, customer, staff, manager); skip Week 3 sample data',
        )

    def handle(self, *args, **options):
        skip_sample = options['no_sample']

        self.stdout.write(self.style.SUCCESS('\n=== Seeding MultiBook data ===\n'))

        # 1. Admin (superuser)
        admin_email = 'admin@multibook.local'
        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'username': admin_email,
            },
        )
        if created:
            admin.set_password(DEFAULT_ADMIN_PASSWORD)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'  [OK] Admin user: {admin_email} (password: {DEFAULT_ADMIN_PASSWORD})'))
        else:
            self.stdout.write(f'  - Admin already exists: {admin_email}')

        # 2. Manager user + Manager profile
        manager_email = 'manager@multibook.local'
        manager_user, created = User.objects.get_or_create(
            email=manager_email,
            defaults={
                'role': 'manager',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'username': manager_email,
            },
        )
        if created:
            manager_user.set_password(DEFAULT_MANAGER_PASSWORD)
            manager_user.save()
            self.stdout.write(self.style.SUCCESS(f'  [OK] Manager user: {manager_email}'))
        else:
            self.stdout.write(f'  - Manager user already exists: {manager_email}')
        Manager.objects.get_or_create(
            user=manager_user,
            defaults={
                'can_manage_all': False,
                'can_manage_customers': True,
                'can_manage_staff': True,
                'can_manage_appointments': True,
                'can_view_reports': True,
                'is_active': True,
            },
        )

        # 3. Customer user + Customer record
        customer_email = 'customer@multibook.test'
        customer_user, created = User.objects.get_or_create(
            email=customer_email,
            defaults={
                'role': 'customer',
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
                'username': customer_email,
            },
        )
        if created:
            customer_user.set_password(DEFAULT_CUSTOMER_PASSWORD)
            customer_user.save()
            self.stdout.write(self.style.SUCCESS(f'  [OK] Customer user: {customer_email} (password: {DEFAULT_CUSTOMER_PASSWORD})'))
        else:
            self.stdout.write(f'  - Customer user already exists: {customer_email}')
        CustomerModel.objects.get_or_create(
            email=customer_email,
            defaults={
                'user': customer_user,
                'name': 'Test Customer',
                'phone': '07700 900000',
                'postcode': 'SW1A 1AA',
                'city': 'London',
                'country': 'United Kingdom',
            },
        )

        # 4. Week 3 sample data (categories, services, staff members, schedules, areas, appointments)
        if not skip_sample:
            self.stdout.write('\nCreating Week 3 sample data (categories, services, staff, areas, appointments)...')
            call_command('create_week3_sample_data', verbosity=1)
            # 5. Staff user linked to first Staff (for staff portal login)
            first_staff = Staff.objects.filter(email__icontains='multibook.test').first()
            if first_staff and not first_staff.user_id:
                staff_email = first_staff.email
                staff_user, created = User.objects.get_or_create(
                    email=staff_email,
                    defaults={
                        'role': 'staff',
                        'is_staff': False,
                        'is_superuser': False,
                        'is_active': True,
                        'username': staff_email,
                    },
                )
                if created:
                    staff_user.set_password(DEFAULT_STAFF_PASSWORD)
                    staff_user.save()
                    first_staff.user = staff_user
                    first_staff.save()
                    self.stdout.write(self.style.SUCCESS(f'  [OK] Staff user for portal: {staff_email} (password: {DEFAULT_STAFF_PASSWORD})'))
        else:
            self.stdout.write('  (Skipped Week 3 sample data; use --no-sample to only create users)')

        self.stdout.write(self.style.SUCCESS('\n=== Seed complete ==='))
        self.stdout.write('Users: admin@multibook.local, manager@multibook.local, customer@multibook.test')
        if not skip_sample:
            self.stdout.write('Staff portal: use first staff email (e.g. john.smith@multibook.test) with password from SEED_STAFF_PASSWORD or default.')
        self.stdout.write('Change default passwords in production (SEED_* env vars).')
