"""
Delete all users except the admin user.
Run this script to clean up the database and keep only the admin user.
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

# Get admin user
admin_username = 'admin'
try:
    admin_user = User.objects.get(username=admin_username)
    admin_id = admin_user.id
    print(f"Keeping admin user: {admin_user.username} ({admin_user.email})")
except User.DoesNotExist:
    print(f"ERROR: Admin user '{admin_username}' not found!")
    print("Aborting deletion to prevent deleting all users.")
    sys.exit(1)

# Get all users except admin
other_users = User.objects.exclude(id=admin_id)
count = other_users.count()

if count == 0:
    print("\nNo other users to delete. Only admin user exists.")
    sys.exit(0)

print(f"\nFound {count} user(s) to delete:")
for user in other_users:
    print(f"  - {user.username} ({user.email}) - Role: {user.role}")

# Confirm deletion
print(f"\n[WARNING] This will delete {count} user(s) from the database!")
response = input("Are you sure you want to continue? (yes/no): ").strip().lower()

if response != 'yes':
    print("Deletion cancelled.")
    sys.exit(0)

# Delete users
deleted_count, _ = other_users.delete()

print(f"\n[SUCCESS] Deleted {deleted_count} user(s) from the database.")
print(f"Admin user '{admin_username}' is still in the database.")
