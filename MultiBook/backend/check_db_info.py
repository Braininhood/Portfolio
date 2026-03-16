"""
Script to check what data is saved in the database from Week 1.
Handles missing tables gracefully.
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

User = get_user_model()

print("=" * 80)
print("WEEK 1 DATABASE INFORMATION CHECK")
print("=" * 80)
print()

# Get all tables
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

print(f"Total tables in database: {len(tables)}")
print()
print("=== ALL TABLES AND RECORD COUNTS ===")
print()

# Check each table
for table_name in tables:
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            print(f"[TABLE] {table_name}")
            print(f"   Records: {count}")
            print(f"   Columns: {len(col_names)} ({', '.join(col_names[:5])}{'...' if len(col_names) > 5 else ''})")
            
            # Show sample data for non-empty tables
            if count > 0 and count <= 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                print(f"   Sample data:")
                for i, row in enumerate(rows, 1):
                    # Show first few fields
                    row_data = dict(zip(col_names, row))
                    # Filter out sensitive/password fields
                    safe_data = {k: v for k, v in row_data.items() 
                                if k not in ['password', 'calendar_access_token', 'calendar_refresh_token']}
                    # Show only first 3 fields
                    preview = {k: str(v)[:50] for k, v in list(safe_data.items())[:3]}
                    print(f"      Row {i}: {preview}")
            elif count > 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                row = cursor.fetchone()
                if row:
                    row_data = dict(zip(col_names, row))
                    safe_data = {k: v for k, v in row_data.items() 
                                if k not in ['password', 'calendar_access_token', 'calendar_refresh_token']}
                    preview = {k: str(v)[:50] for k, v in list(safe_data.items())[:3]}
                    print(f"   Sample row: {preview}")
            print()
    except Exception as e:
        print(f"[ERROR] {table_name}: Error - {str(e)}")
        print()

# Check for specific Week 1 models
print("=" * 80)
print("WEEK 1 MODEL STATUS")
print("=" * 80)
print()

week1_models = {
    'accounts_user': 'User model',
    'accounts_profile': 'Profile model',
    'accounts_manager': 'Manager model',
    'services_category': 'Category model',
    'services_service': 'Service model',
    'staff_staff': 'Staff model',
    'staff_staffschedule': 'StaffSchedule model',
    'staff_staffarea': 'StaffArea model',
    'customers_customer': 'Customer model',
    'customers_address': 'Address model',
    'appointments_appointment': 'Appointment model',
    'appointments_customerappointment': 'CustomerAppointment model',
    'orders_order': 'Order model',
    'orders_orderitem': 'OrderItem model',
    'subscriptions_subscription': 'Subscription model',
    'subscriptions_subscriptionappointment': 'SubscriptionAppointment model',
}

for table_name, model_name in week1_models.items():
    if table_name in tables:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
        print(f"[OK] {model_name}: Table exists ({count} records)")
    else:
        print(f"[MISSING] {model_name}: Table does NOT exist (migration not applied)")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("Week 1 created the following database structure:")
print("  [MODEL] User model (accounts_user) - Custom user with roles")
print("  [MODEL] Profile model (accounts_profile) - User profiles with calendar sync fields")
print("  [MODEL] Manager model (accounts_manager) - Manager permissions")
print("  [MODEL] Category model (services_category) - Service categories")
print("  [MODEL] Service model (services_service) - Services")
print("  [MODEL] Staff model (staff_staff) - Staff members")
print("  [MODEL] StaffSchedule model (staff_staffschedule) - Staff working hours")
print("  [MODEL] StaffArea model (staff_staffarea) - Staff service areas")
print("  [MODEL] Customer model (customers_customer) - Customers")
print("  [MODEL] Address model (customers_address) - Customer addresses")
print("  [MODEL] Appointment model (appointments_appointment) - Appointments")
print("  [MODEL] CustomerAppointment model (appointments_customerappointment) - Customer bookings")
print("  [MODEL] Order model (orders_order) - Orders with guest checkout")
print("  [MODEL] OrderItem model (orders_orderitem) - Order items")
print("  [MODEL] Subscription model (subscriptions_subscription) - Subscriptions")
print("  [MODEL] SubscriptionAppointment model (subscriptions_subscriptionappointment) - Subscription appointments")
print()
print("Note: Some tables may not exist yet if migrations haven't been run.")
print("Run 'python manage.py makemigrations' and 'python manage.py migrate' to create all tables.")
print()
print("=" * 80)
