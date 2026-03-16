# PostgreSQL Database Setup for MultiBook

This guide will help you create the PostgreSQL database locally for the MultiBook project.

## Prerequisites

- PostgreSQL is installed and running on your system
- You have PostgreSQL superuser credentials (usually `postgres` user)

## Quick Setup (Recommended)

### Option 1: Using Python Script (Recommended)

1. Make sure you have `psycopg2-binary` installed:
   ```powershell
   pip install psycopg2-binary
   ```

2. Run the setup script with your PostgreSQL superuser password:
   ```powershell
   python setup_postgres_db.py postgres <your_postgres_password>
   ```
   
   Example:
   ```powershell
   python setup_postgres_db.py postgres mypassword
   ```

### Option 2: Using PowerShell Script (Easiest)

Use the provided PowerShell script that uses the correct psql path:

```powershell
cd backend
.\create_postgres_db.ps1
```

This script will:
- Use the correct psql path: `C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\psql.exe`
- Prompt you for the PostgreSQL superuser password
- Create the database, user, and grant all necessary privileges

### Option 3: Using SQL Script with psql

1. Use the psql path: `C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\psql.exe`

2. Run the SQL script:
   ```powershell
   & "C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\psql.exe" -U postgres -f create_db.sql
   ```

3. You'll be prompted for the PostgreSQL superuser password.

### Option 4: Manual Setup

1. Connect to PostgreSQL:
   ```powershell
   psql -U postgres
   ```
   
   Or use pgAdmin or another PostgreSQL client.

2. Run the following SQL commands:
   ```sql
   -- Create user
   CREATE USER multibook_user WITH PASSWORD 'multibook_pass';
   
   -- Create database
   CREATE DATABASE multibook_db OWNER multibook_user;
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE multibook_db TO multibook_user;
   
   -- Connect to new database
   \c multibook_db
   
   -- Grant schema privileges
   GRANT ALL ON SCHEMA public TO multibook_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO multibook_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO multibook_user;
   ```

## Database Details

After setup, you'll have:

- **Database Name**: `multibook_db`
- **Database User**: `multibook_user`
- **Password**: `multibook_pass`
- **Host**: `localhost`
- **Port**: `5432`

**Connection String:**
```
postgresql://multibook_user:multibook_pass@localhost:5432/multibook_db
```

## Next Steps

1. Update your `.env` file in the `backend` directory:
   ```
   DATABASE_URL=postgresql://multibook_user:multibook_pass@localhost:5432/multibook_db
   ```

2. Update Django settings if needed (should work automatically if using `DATABASE_URL`)

3. Run migrations:
   ```powershell
   python manage.py migrate
   ```

4. Create superuser:
   ```powershell
   python manage.py createsuperuser
   ```

## Troubleshooting

### Error: "password authentication failed"
- Make sure you're using the correct PostgreSQL superuser password
- If you've forgotten your password, you may need to reset it in PostgreSQL configuration

### Error: "could not connect to server"
- Make sure PostgreSQL is running
- Check if PostgreSQL is listening on port 5432: `Test-NetConnection -ComputerName localhost -Port 5432`

### Error: "psql: command not found"
- Add PostgreSQL bin directory to your PATH, or use the full path to psql.exe
- Or use the Python script instead (Option 1)

### Error: "database already exists"
- The script will drop and recreate the database if it exists
- If you want to keep existing data, modify the script to skip database creation
