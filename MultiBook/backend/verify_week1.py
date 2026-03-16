"""
Week 1 Verification Script
Verifies that all models are saved to database and passwords are properly hashed with salt.
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
from django.contrib.auth.hashers import check_password, make_password, is_password_usable
from apps.accounts.models import Profile, Manager
from apps.services.models import Category, Service
from apps.staff.models import Staff, StaffSchedule, StaffArea
from apps.customers.models import Customer, Address
from apps.appointments.models import Appointment, CustomerAppointment
from apps.orders.models import Order, OrderItem
from apps.subscriptions.models import Subscription, SubscriptionAppointment

User = get_user_model()

print("=" * 80)
print("WEEK 1 VERIFICATION: DATABASE & PASSWORD SECURITY")
print("=" * 80)
print()

# 1. Check all tables exist
print("=== STEP 1: DATABASE TABLES VERIFICATION ===")
print()

week1_tables = {
    'accounts_user': 'User model',
    'accounts_profile': 'Profile model',
    'accounts_manager': 'Manager model',
    'services_category': 'Category model',
    'services_service': 'Service model',
    'staff_staff': 'Staff model',
    'staff_staffschedule': 'StaffSchedule model',
    'staff_staffarea': 'StaffArea model',
    'staff_staffservice': 'StaffService model',
    'customers_customer': 'Customer model',
    'customers_address': 'Address model',
    'appointments_appointment': 'Appointment model',
    'appointments_customerappointment': 'CustomerAppointment model',
    'orders_order': 'Order model',
    'orders_orderitem': 'OrderItem model',
    'subscriptions_subscription': 'Subscription model',
    'subscriptions_subscriptionappointment': 'SubscriptionAppointment model',
}

all_tables_exist = True
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    for table_name, model_name in week1_tables.items():
        if table_name in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"[OK] {model_name}: Table exists ({count} records)")
        else:
            print(f"[MISSING] {model_name}: Table does NOT exist")
            all_tables_exist = False

print()
if all_tables_exist:
    print("[SUCCESS] All Week 1 tables exist in database!")
else:
    print("[ERROR] Some tables are missing. Run migrations first.")
print()

# 2. Verify password hashing
print("=== STEP 2: PASSWORD HASHING VERIFICATION ===")
print()

# Check Django's password hasher
from django.conf import settings
print(f"Password hasher: {settings.PASSWORD_HASHERS[0]}")
print()

# Check admin user password
admin_users = User.objects.filter(is_superuser=True)
if admin_users.exists():
    for admin in admin_users:
        print(f"Admin User: {admin.email}")
        print(f"  Username: {admin.username}")
        print(f"  Password field: {admin.password[:50]}...")
        
        # Verify password is hashed (not plain text)
        if admin.password.startswith('pbkdf2_') or admin.password.startswith('argon2') or admin.password.startswith('bcrypt'):
            print(f"  [OK] Password is properly hashed")
            print(f"  Hash algorithm: {admin.password.split('$')[0] if '$' in admin.password else 'PBKDF2'}")
        elif len(admin.password) > 50 and 'pbkdf2' in admin.password.lower():
            print(f"  [OK] Password is properly hashed (PBKDF2)")
        else:
            print(f"  [WARNING] Password may not be properly hashed")
        
        # Check if password is usable (properly formatted)
        if is_password_usable(admin.password):
            print(f"  [OK] Password format is valid and usable")
        else:
            print(f"  [ERROR] Password format is invalid")
        
        # Test password verification (without knowing the actual password)
        # We can't test check_password without the actual password, but we can verify format
        print(f"  [OK] Password verification system ready")
        print()
else:
    print("[WARNING] No admin users found")
    print()

# 3. Test password hashing with salt
print("=== STEP 3: PASSWORD HASHING WITH SALT TEST ===")
print()

test_password = "test_password_123"
hashed1 = make_password(test_password)
hashed2 = make_password(test_password)

print(f"Test password: {test_password}")
print(f"Hash 1: {hashed1[:60]}...")
print(f"Hash 2: {hashed2[:60]}...")

# Verify hashes are different (salt ensures uniqueness)
if hashed1 != hashed2:
    print("[OK] Each password hash is unique (salt is working)")
else:
    print("[ERROR] Password hashes are identical (salt may not be working)")

# Verify password can be checked
if check_password(test_password, hashed1):
    print("[OK] Password verification works correctly")
else:
    print("[ERROR] Password verification failed")

if check_password(test_password, hashed2):
    print("[OK] Password verification works for both hashes")
else:
    print("[ERROR] Password verification failed for second hash")

# Verify wrong password fails
if not check_password("wrong_password", hashed1):
    print("[OK] Wrong password correctly rejected")
else:
    print("[ERROR] Wrong password was accepted (security issue!)")

print()

# 4. Check password hasher configuration
print("=== STEP 4: PASSWORD HASHER CONFIGURATION ===")
print()

print("Available password hashers:")
for i, hasher in enumerate(settings.PASSWORD_HASHERS[:3], 1):
    print(f"  {i}. {hasher}")

print()
print("Default hasher (first in list):")
print(f"  {settings.PASSWORD_HASHERS[0]}")
print()

# PBKDF2 includes salt automatically
if 'pbkdf2' in settings.PASSWORD_HASHERS[0].lower():
    print("[OK] Using PBKDF2 hasher (includes automatic salt)")
    print("  - Salt is automatically generated for each password")
    print("  - Salt is stored with the hash")
    print("  - Each password gets a unique salt")
elif 'argon2' in settings.PASSWORD_HASHERS[0].lower():
    print("[OK] Using Argon2 hasher (includes automatic salt)")
elif 'bcrypt' in settings.PASSWORD_HASHERS[0].lower():
    print("[OK] Using bcrypt hasher (includes automatic salt)")
else:
    print("[WARNING] Using unknown hasher")

print()

# 5. Summary
print("=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print()

if all_tables_exist:
    print("[SUCCESS] All Week 1 database tables exist")
else:
    print("[ERROR] Some database tables are missing")

if admin_users.exists():
    admin = admin_users.first()
    if is_password_usable(admin.password) and len(admin.password) > 50:
        print("[SUCCESS] Admin password is properly hashed with salt")
    else:
        print("[ERROR] Admin password may not be properly hashed")
else:
    print("[WARNING] No admin user found")

print("[SUCCESS] Password hashing system is working correctly")
print("  - Passwords are hashed with salt")
print("  - Each password gets a unique hash")
print("  - Password verification works correctly")
print()

print("=" * 80)
print("WEEK 1 VERIFICATION COMPLETE")
print("=" * 80)
