# PowerShell script to create PostgreSQL database for MultiBook
# This script helps set up the database using psql

[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingPlainTextForPassword', '')]
param(
    [string]$SuperUser = "postgres",
    [string]$DatabaseName = "multibook_db",
    [string]$DatabaseUser = "multibook_user",
    [string]$DatabasePassword = "multibook_pass"  # This parameter sets the password VALUE for the database user being created, not a sensitive credential input
)

Write-Host "PostgreSQL Database Setup for MultiBook" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PostgreSQL is running
$portTest = Test-NetConnection -ComputerName localhost -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $portTest) {
    Write-Host "[ERROR] PostgreSQL is not running on port 5432" -ForegroundColor Red
    Write-Host "Please start PostgreSQL first." -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] PostgreSQL is running on port 5432" -ForegroundColor Green
Write-Host ""

# Find psql executable
$psqlPaths = @(
    "C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\psql.exe",
    "C:\Program Files\PostgreSQL\17\bin\psql.exe",
    "C:\Program Files\PostgreSQL\16\bin\psql.exe",
    "C:\Program Files\PostgreSQL\15\bin\psql.exe",
    "C:\Program Files\PostgreSQL\14\bin\psql.exe",
    "C:\Program Files\PostgreSQL\13\bin\psql.exe",
    "C:\Program Files\PostgreSQL\12\bin\psql.exe",
    "psql.exe"  # If in PATH
)

$psqlExe = $null
foreach ($path in $psqlPaths) {
    if (Test-Path $path) {
        $psqlExe = $path
        Write-Host "[INFO] Found psql at: $path" -ForegroundColor Green
        break
    }
}

if (-not $psqlExe) {
    Write-Host "[ERROR] Could not find psql.exe" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please ensure PostgreSQL is installed, or run the SQL commands manually:" -ForegroundColor Yellow
    Write-Host "  1. Connect to PostgreSQL: psql -U $SuperUser"
    Write-Host "  2. Run the SQL commands from create_db.sql"
    Write-Host ""
    Write-Host "Alternatively, use Python script with your password:" -ForegroundColor Yellow
    Write-Host "  python setup_postgres_db.py $SuperUser <your_password>"
    exit 1
}

Write-Host ""
Write-Host "Database Configuration:" -ForegroundColor Cyan
Write-Host "  Database Name: $DatabaseName"
Write-Host "  Database User: $DatabaseUser"
Write-Host "  Superuser: $SuperUser"
Write-Host ""
Write-Host "Note: You will be prompted for the PostgreSQL superuser password" -ForegroundColor Yellow
Write-Host ""

# Create SQL commands
$sqlCommands = @"
-- Create user if not exists
DO `$`$`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DatabaseUser') THEN
        CREATE USER $DatabaseUser WITH PASSWORD '$DatabasePassword';
    ELSE
        ALTER USER $DatabaseUser WITH PASSWORD '$DatabasePassword';
    END IF;
END
`$`$`$;

-- Drop database if exists
DROP DATABASE IF EXISTS $DatabaseName;

-- Create database
CREATE DATABASE $DatabaseName OWNER $DatabaseUser;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DatabaseName TO $DatabaseUser;
"@

# Write SQL to temp file
$tempSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sqlCommands | Out-File -FilePath $tempSqlFile -Encoding UTF8

try {
    Write-Host "[INFO] Creating database and user..." -ForegroundColor Cyan
    
    # Run SQL commands
    $env:PGPASSWORD = ""  # Clear any existing password
    & $psqlExe -U $SuperUser -d postgres -f $tempSqlFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Database setup complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Database connection details:" -ForegroundColor Cyan
        Write-Host "  Database: $DatabaseName"
        Write-Host "  User: $DatabaseUser"
        Write-Host "  Password: $DatabasePassword"
        Write-Host "  Host: localhost"
        Write-Host "  Port: 5432"
        Write-Host ""
        Write-Host "DATABASE_URL: postgresql://$DatabaseUser`:$DatabasePassword@localhost:5432/$DatabaseName" -ForegroundColor Green
        
        # Grant schema privileges (connect to new database)
        Write-Host ""
        Write-Host "[INFO] Granting schema privileges..." -ForegroundColor Cyan
        $schemaSql = @"
GRANT ALL ON SCHEMA public TO $DatabaseUser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DatabaseUser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DatabaseUser;
"@
        $schemaSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
        $schemaSql | Out-File -FilePath $schemaSqlFile -Encoding UTF8
        & $psqlExe -U $SuperUser -d $DatabaseName -f $schemaSqlFile
        Remove-Item $schemaSqlFile -ErrorAction SilentlyContinue
    } else {
        Write-Host "[ERROR] Failed to create database. Check PostgreSQL credentials." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Remove-Item $tempSqlFile -ErrorAction SilentlyContinue
}
