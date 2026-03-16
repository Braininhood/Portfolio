"""
Verify that all Day 5: Database Models requirements are complete on PostgreSQL.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model
from django.apps import apps

User = get_user_model()

print("=" * 80)
print("VERIFYING DAY 5: DATABASE MODELS REQUIREMENTS")
print("=" * 80)
print()

# Check database type
print("1. Database Configuration:")
db_engine = connection.settings_dict['ENGINE']
db_name = connection.settings_dict['NAME']
if 'postgresql' in db_engine:
    print(f"   [OK] Using PostgreSQL database: {db_name}")
else:
    print(f"   [WARNING] Using {db_engine}, expected PostgreSQL")

print()
print("2. Models Check:")
print("-" * 80)

requirements = {
    'User and Profile models': ['accounts.user', 'accounts.profile'],
    'Manager model': ['accounts.manager'],
    'Service and Category models': ['services.service', 'services.category'],
    'Staff and StaffSchedule models': ['staff.staff', 'staff.staffschedule'],
    'StaffArea model': ['staff.staffarea'],
    'Customer model': ['customers.customer'],
    'Appointment and CustomerAppointment models': ['appointments.appointment', 'appointments.customerappointment'],
}

all_ok = True
for requirement, model_names in requirements.items():
    found = []
    missing = []
    for model_name in model_names:
        app_label, model_name_only = model_name.split('.')
        try:
            model = apps.get_model(app_label, model_name_only)
            found.append(model_name)
        except LookupError:
            missing.append(model_name)
    
    if missing:
        print(f"   [FAIL] {requirement}")
        print(f"          Missing: {', '.join(missing)}")
        all_ok = False
    else:
        print(f"   [OK] {requirement}")
        print(f"        Models: {', '.join(found)}")

print()
print("3. Calendar Sync Fields Check:")
print("-" * 80)

# Check Profile calendar sync fields
try:
    Profile = apps.get_model('accounts', 'profile')
    profile_fields = [f.name for f in Profile._meta.get_fields()]
    calendar_fields = [
        'calendar_sync_enabled',
        'calendar_provider',
        'calendar_access_token',
        'calendar_refresh_token',
        'calendar_calendar_id',
        'calendar_sync_settings'
    ]
    
    missing_fields = [f for f in calendar_fields if f not in profile_fields]
    if missing_fields:
        print(f"   [FAIL] Profile calendar sync fields")
        print(f"          Missing: {', '.join(missing_fields)}")
        all_ok = False
    else:
        print(f"   [OK] Profile calendar sync fields present")
        print(f"        Fields: {', '.join(calendar_fields)}")
except LookupError:
    print(f"   [FAIL] Profile model not found")
    all_ok = False

# Check Appointment calendar fields
try:
    Appointment = apps.get_model('appointments', 'appointment')
    appointment_fields = [f.name for f in Appointment._meta.get_fields()]
    if 'calendar_event_id' in appointment_fields and 'calendar_synced_to' in appointment_fields:
        print(f"   [OK] Appointment calendar fields present")
        print(f"        Fields: calendar_event_id, calendar_synced_to")
    else:
        missing = []
        if 'calendar_event_id' not in appointment_fields:
            missing.append('calendar_event_id')
        if 'calendar_synced_to' not in appointment_fields:
            missing.append('calendar_synced_to')
        print(f"   [FAIL] Appointment calendar fields")
        print(f"          Missing: {', '.join(missing)}")
        all_ok = False
except LookupError:
    print(f"   [FAIL] Appointment model not found")
    all_ok = False

print()
print("4. Manager Model Permissions Check:")
print("-" * 80)

try:
    Manager = apps.get_model('accounts', 'manager')
    manager_fields = [f.name for f in Manager._meta.get_fields()]
    permission_fields = [
        'permissions',
        'can_manage_all',
        'can_manage_customers',
        'can_manage_staff',
        'can_manage_appointments',
        'can_view_reports'
    ]
    
    missing_fields = [f for f in permission_fields if f not in manager_fields]
    if missing_fields:
        print(f"   [FAIL] Manager permission fields")
        print(f"          Missing: {', '.join(missing_fields)}")
        all_ok = False
    else:
        print(f"   [OK] Manager permission fields present")
        print(f"        Fields: {', '.join(permission_fields)}")
except LookupError:
    print(f"   [FAIL] Manager model not found")
    all_ok = False

print()
print("5. Migrations Status:")
print("-" * 80)

from django.db.migrations.recorder import MigrationRecorder
Migration = MigrationRecorder.Migration

app_labels = ['accounts', 'services', 'staff', 'customers', 'appointments']
for app_label in app_labels:
    try:
        migrations = Migration.objects.filter(app=app_label).count()
        print(f"   [OK] {app_label}: {migrations} migration(s) applied")
    except Exception as e:
        print(f"   [WARNING] {app_label}: Could not check migrations")

print()
print("6. Admin Superuser Check:")
print("-" * 80)

try:
    admin_users = User.objects.filter(is_superuser=True, is_staff=True)
    if admin_users.exists():
        admin = admin_users.first()
        print(f"   [OK] Admin superuser exists")
        print(f"        Username: {admin.username}")
        print(f"        Email: {admin.email}")
        print(f"        Role: {admin.role}")
        print(f"        Verified: {admin.is_verified}")
    else:
        print(f"   [FAIL] No admin superuser found")
        all_ok = False
except Exception as e:
    print(f"   [WARNING] Could not check admin user: {e}")

print()
print("7. Database Tables Check:")
print("-" * 80)

cursor = connection.cursor()
cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND (
        tablename LIKE 'accounts_%' OR 
        tablename LIKE 'services_%' OR 
        tablename LIKE 'staff_%' OR 
        tablename LIKE 'customers_%' OR 
        tablename LIKE 'appointments_%'
    )
    ORDER BY tablename
""")
tables = [row[0] for row in cursor.fetchall()]

if tables:
    print(f"   [OK] Found {len(tables)} database tables")
    print(f"        Tables: {', '.join(tables)}")
else:
    print(f"   [FAIL] No database tables found")
    all_ok = False

print()
print("=" * 80)
if all_ok:
    print("RESULT: ALL DAY 5 REQUIREMENTS COMPLETE ON POSTGRESQL! [OK]")
else:
    print("RESULT: SOME REQUIREMENTS MISSING [WARNING]")
print("=" * 80)
