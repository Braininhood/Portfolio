"""
Script to create PostgreSQL database and user for MultiBook project.
Run this script to set up the database locally.

Usage:
    python setup_postgres_db.py [superuser] [superuser_password]
    
If no arguments provided, defaults to:
    superuser: postgres
    superuser_password: (will prompt, or use empty string for trust auth)
"""

import psycopg2
from psycopg2 import sql
import sys

# Database configuration
DB_NAME = 'multibook_db'
DB_USER = 'multibook_user'
DB_PASSWORD = 'multibook_pass'

def create_database(superuser='postgres', superuser_password=''):
    """Create PostgreSQL database and user."""
    
    print("Setting up PostgreSQL database for MultiBook...")
    print(f"Using superuser: {superuser}")
    
    # First, connect to postgres database to create new database
    try:
        print("\nConnecting to PostgreSQL as superuser...")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user=superuser,
            password=superuser_password if superuser_password else None
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (DB_USER,)
        )
        if cursor.fetchone():
            print(f"User '{DB_USER}' already exists. Updating password...")
            cursor.execute(
                sql.SQL("ALTER USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_USER)
                ),
                (DB_PASSWORD,)
            )
        else:
            # Create user
            print(f"Creating user '{DB_USER}'...")
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(DB_USER)
                ),
                (DB_PASSWORD,)
            )
        print(f"User '{DB_USER}' ready.")
        
        # Drop database if exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        if cursor.fetchone():
            print(f"Dropping existing database '{DB_NAME}'...")
            # Terminate existing connections
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                (DB_NAME,)
            )
            cursor.execute(
                sql.SQL("DROP DATABASE {}").format(
                    sql.Identifier(DB_NAME)
                )
            )
            print(f"Database '{DB_NAME}' dropped.")
        
        # Create database
        print(f"Creating database '{DB_NAME}'...")
        cursor.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            )
        )
        print(f"Database '{DB_NAME}' created with owner '{DB_USER}'.")
        
        # Grant privileges
        print(f"Granting privileges...")
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            )
        )
        
        # Connect to new database to grant schema privileges
        conn.close()
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database=DB_NAME,
            user=superuser,
            password=superuser_password if superuser_password else None
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(
            sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        cursor.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        
        conn.close()
        
        print("\n[SUCCESS] Database setup complete!")
        print("\nDatabase connection details:")
        print(f"  Database: {DB_NAME}")
        print(f"  User: {DB_USER}")
        print(f"  Password: {DB_PASSWORD}")
        print(f"  Host: localhost")
        print(f"  Port: 5432")
        print(f"\nDATABASE_URL: postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}")
        
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Error connecting to PostgreSQL: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. You need to provide the PostgreSQL superuser password")
        print("   Usage: python setup_postgres_db.py postgres <your_password>")
        print("3. Verify PostgreSQL is listening on port 5432")
        print("\nAlternative: Use the SQL script create_db.sql with psql:")
        print('   psql -U postgres -f create_db.sql')
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(0)

if __name__ == '__main__':
    superuser = sys.argv[1] if len(sys.argv) > 1 else 'postgres'
    superuser_password = sys.argv[2] if len(sys.argv) > 2 else ''
    create_database(superuser, superuser_password)
