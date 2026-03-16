"""
Output all Django migration SQL in dependency order (PostgreSQL).
Use: python manage.py export_schema_sql -o supabase_schema.sql
Then run the generated file in Supabase SQL Editor to create all tables.
Requires DATABASE_URL (or default DB) to be PostgreSQL for correct SQL dialect.
"""
from io import StringIO
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection

# Dependency order for MultiBook migrations (matches Django migration graph)
MIGRATION_ORDER = [
    ('contenttypes', '0001_initial'),
    ('contenttypes', '0002_remove_content_type_name'),
    ('auth', '0001_initial'),
    ('auth', '0002_alter_permission_name_max_length'),
    ('auth', '0003_alter_user_email_max_length'),
    ('auth', '0004_alter_user_username_opts'),
    ('auth', '0005_alter_user_last_login_null'),
    ('auth', '0006_require_contenttypes_0002'),
    ('auth', '0007_alter_validators_add_error_messages'),
    ('auth', '0008_alter_user_username_max_length'),
    ('auth', '0009_alter_user_last_name_max_length'),
    ('auth', '0010_alter_group_name_max_length'),
    ('auth', '0011_update_proxy_permissions'),
    ('auth', '0012_alter_user_first_name_max_length'),
    ('sessions', '0001_initial'),
    ('admin', '0001_initial'),
    ('admin', '0002_logentry_remove_auto_add'),
    ('admin', '0003_logentry_add_action_flag_choices'),
    ('services', '0001_initial'),
    ('customers', '0001_initial'),
    ('accounts', '0001_initial'),
    ('staff', '0001_initial'),
    ('appointments', '0001_initial'),
    ('orders', '0001_initial'),
    ('appointments', '0002_initial'),
    ('subscriptions', '0001_initial'),
    ('orders', '0002_changerequest'),
    ('accounts', '0002_manager_managed_customers_manager_managed_staff'),
    ('accounts', '0003_alter_manager_is_active_and_more'),
    ('staff', '0002_convert_radius_to_miles'),
    ('coupons', '0001_initial'),
]


class Command(BaseCommand):
    help = 'Export all migration SQL in dependency order to a file (PostgreSQL).'

    def add_arguments(self, parser):
        parser.add_argument(
            '-o', '--output',
            type=str,
            default='supabase_schema.sql',
            help='Output SQL file path (default: supabase_schema.sql)',
        )

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stderr.write(
                self.style.ERROR('Database must be PostgreSQL. Set DATABASE_URL to Supabase/Postgres.')
            )
            return

        out_path = options['output']
        buf = StringIO()
        buf.write('-- MultiBook schema: all tables for Supabase (PostgreSQL)\n')
        buf.write('-- Generated from Django migrations in dependency order.\n')
        buf.write('-- Run this in Supabase Dashboard -> SQL Editor if you cannot run Django migrate.\n\n')

        for app_label, migration_name in MIGRATION_ORDER:
            self.stdout.write(f'  {app_label} {migration_name}')
            cmd_out = StringIO()
            try:
                call_command('sqlmigrate', app_label, migration_name, stdout=cmd_out)
            except Exception as e:
                self.stderr.write(self.style.WARNING(f'  Skip {app_label} {migration_name}: {e}'))
                continue
            sql = cmd_out.getvalue()
            if sql.strip():
                buf.write(f'-- {app_label}.{migration_name}\n')
                buf.write(sql)
                if not sql.endswith('\n'):
                    buf.write('\n')
                buf.write('\n')

        sql_content = buf.getvalue()
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        self.stdout.write(self.style.SUCCESS(f'Wrote {len(sql_content)} chars to {out_path}'))
