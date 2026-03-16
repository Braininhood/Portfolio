-- SQL script to create PostgreSQL database and user for MultiBook project
-- Run this script as PostgreSQL superuser (usually 'postgres')

-- Create user if not exists (PostgreSQL doesn't support IF NOT EXISTS for users)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'multibook_user') THEN
        CREATE USER multibook_user WITH PASSWORD 'multibook_pass';
    ELSE
        ALTER USER multibook_user WITH PASSWORD 'multibook_pass';
    END IF;
END
$$;

-- Drop database if exists (use with caution!)
DROP DATABASE IF EXISTS multibook_db;

-- Create database
CREATE DATABASE multibook_db OWNER multibook_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE multibook_db TO multibook_user;

-- Connect to the new database and grant schema privileges
\c multibook_db
GRANT ALL ON SCHEMA public TO multibook_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO multibook_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO multibook_user;
