"""
Script to reset admin/superuser password after database migration.
Run this to set a known password for admin users.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("Resetting Admin/Superuser Passwords")
print("=" * 80)
print()

# Find all superusers
superusers = User.objects.filter(is_superuser=True)
print(f"Found {superusers.count()} superuser(s):")

for user in superusers:
    print(f"  - {user.username} ({user.email})")
    
    # Reset password to 'admin123'
    user.set_password('admin123')
    user.save()
    print(f"    ✓ Password reset to: admin123")

# Find all staff users
staff_users = User.objects.filter(is_staff=True, is_superuser=False)
if staff_users.exists():
    print(f"\nFound {staff_users.count()} staff user(s):")
    for user in staff_users:
        print(f"  - {user.username} ({user.email})")
        user.set_password('admin123')
        user.save()
        print(f"    ✓ Password reset to: admin123")

print("\n" + "=" * 80)
print("Password reset complete!")
print("\nDefault password for all admin/staff users: admin123")
print("Please change these passwords after logging in!")
print("=" * 80)
