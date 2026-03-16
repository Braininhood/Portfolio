"""
Script to fix users after database migration - set superuser flags and reset passwords.
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
print("Fixing Users After Migration")
print("=" * 80)
print()

# Get all users
users = User.objects.all()
print(f"Found {users.count()} user(s):\n")

for user in users:
    print(f"User: {user.username} ({user.email})")
    print(f"  Current: superuser={user.is_superuser}, staff={user.is_staff}, active={user.is_active}")
    
    # If username is 'admin' or email contains 'admin', make it a superuser
    if 'admin' in user.username.lower() or 'admin' in user.email.lower():
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        print(f"  Updated: superuser={user.is_superuser}, staff={user.is_staff}, active={user.is_active}")
    
    # Reset password (use env var or default for local dev only - change in production!)
    default_pw = os.environ.get('FIX_USERS_PASSWORD', 'ChangeMe123!')
    user.set_password(default_pw)
    user.save()
    print(f"  ✓ Password reset (use FIX_USERS_PASSWORD env to override)")
    print()

print("=" * 80)
print("All users fixed!")
print("\nPassword set via FIX_USERS_PASSWORD env or default. Change in production!")
print("=" * 80)
