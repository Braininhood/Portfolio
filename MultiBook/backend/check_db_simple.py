"""
Simple script to check what tables exist in the database.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection

print("=" * 80)
print("DATABASE TABLES CHECK")
print("=" * 80)
print()

# Get all tables
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = cursor.fetchall()

print(f"Total tables in database: {len(tables)}")
print()
print("=== ALL TABLES ===")
for table in tables:
    table_name = table[0]
    # Count rows
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f"  - {table_name}: {count} records")
    
    # Show first few columns
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    if columns:
        col_names = [col[1] for col in columns[:5]]  # First 5 columns
        print(f"    Columns: {', '.join(col_names)}{'...' if len(columns) > 5 else ''}")
    print()

print("=" * 80)
print("CHECK COMPLETE")
print("=" * 80)
