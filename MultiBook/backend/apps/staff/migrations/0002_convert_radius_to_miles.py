# Generated migration - Convert radius from kilometers to miles

from django.db import migrations, models
from decimal import Decimal


def _get_radius_column(cursor, connection):
    """Return 'radius_km', 'radius_miles', or None. Works on SQLite and PostgreSQL."""
    if connection.vendor == 'sqlite':
        cursor.execute("PRAGMA table_info(staff_staffarea)")
        for row in cursor.fetchall():
            # row: (cid, name, type, notnull, default, pk)
            if row[1] in ('radius_km', 'radius_miles'):
                return row[1]
        return None
    # PostgreSQL (and MySQL)
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='staff_staffarea'
        AND (column_name='radius_km' OR column_name='radius_miles')
    """)
    row = cursor.fetchone()
    return row[0] if row else None


def convert_km_to_miles(apps, schema_editor):
    """Convert existing radius_km values to miles (km * 0.621371)."""
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        col_name = _get_radius_column(cursor, conn)
        if col_name == 'radius_km':
            cursor.execute("""
                UPDATE staff_staffarea SET radius_km = radius_km * 0.621371
            """)
        elif col_name == 'radius_miles':
            cursor.execute("""
                UPDATE staff_staffarea SET radius_miles = radius_miles * 0.621371
                WHERE radius_miles > 10
            """)


def convert_miles_to_km(apps, schema_editor):
    """Reverse conversion: miles to km (miles / 0.621371)."""
    conn = schema_editor.connection
    with conn.cursor() as cursor:
        col_name = _get_radius_column(cursor, conn)
        if col_name == 'radius_miles':
            cursor.execute("""
                UPDATE staff_staffarea SET radius_miles = radius_miles / 0.621371
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        # Step 1: Convert data from km to miles (works whether field is renamed or not)
        migrations.RunPython(convert_km_to_miles, convert_miles_to_km),
        # Step 2: Rename field if not already renamed
        migrations.RenameField(
            model_name='staffarea',
            old_name='radius_km',
            new_name='radius_miles',
        ),
        # Step 3: Update help text
        migrations.AlterField(
            model_name='staffarea',
            name='radius_miles',
            field=models.DecimalField(
                decimal_places=2,
                help_text='Service radius in miles from center postcode',
                max_digits=5,
            ),
        ),
    ]
