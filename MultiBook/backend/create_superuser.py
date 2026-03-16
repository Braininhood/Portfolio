"""
Create a superuser for the Django admin panel.
Run this script to create an admin user with username 'admin' and password 'admin123'.
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

# Check if admin user already exists
username = 'admin'
email = 'admin@yourdomain.com'
password = 'admin123'

try:
    user = User.objects.get(username=username)
    print(f"User '{username}' already exists. Updating password and permissions...")
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.role = 'admin'  # Set role to admin
    user.is_verified = True  # Admin users are verified by default
    user.email = email
    user.save()
    print(f"[OK] User '{username}' updated successfully!")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  Email: {email}")
except User.DoesNotExist:
    print(f"Creating new superuser '{username}'...")
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    user.role = 'admin'  # Set role to admin
    user.is_verified = True  # Admin users are verified by default
    user.save()
    print(f"[OK] Superuser '{username}' created successfully!")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"  Email: {email}")

print("\nYou can now login to the admin panel at: http://localhost:8000/admin/")
print(f"Username: {username}")
print(f"Password: {password}")
