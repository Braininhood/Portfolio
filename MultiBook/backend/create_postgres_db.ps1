# Quick script to create PostgreSQL database using the correct psql path
# This script will prompt for PostgreSQL password

$psqlPath = "C:\Program Files\PostgreSQL\17\pgAdmin 4\runtime\psql.exe"

if (-not (Test-Path $psqlPath)) {
    Write-Host "[ERROR] psql.exe not found at: $psqlPath" -ForegroundColor Red
    exit 1
}

Write-Host "Creating PostgreSQL database for MultiBook..." -ForegroundColor Cyan
Write-Host "psql path: $psqlPath" -ForegroundColor Gray
Write-Host ""

# Database configuration
$dbName = "multibook_db"
$dbUser = "multibook_user"
$dbPassword = "multibook_pass"
$superUser = "postgres"

# Create SQL commands
$sql = @"
-- Create user if not exists
DO `$`$`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$dbUser') THEN
        CREATE USER $dbUser WITH PASSWORD '$dbPassword';
    ELSE
        ALTER USER $dbUser WITH PASSWORD '$dbPassword';
    END IF;
END
`$`$`$;

-- Drop database if exists
DROP DATABASE IF EXISTS $dbName;

-- Create database
CREATE DATABASE $dbName OWNER $dbUser;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $dbName TO $dbUser;
"@

# Write SQL to temp file
$tempSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sql | Out-File -FilePath $tempSqlFile -Encoding UTF8

Write-Host "Please enter PostgreSQL password for user '$superUser' when prompted..." -ForegroundColor Yellow
Write-Host ""

try {
    # Run SQL commands
    & $psqlPath -U $superUser -d postgres -f $tempSqlFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Database and user created!" -ForegroundColor Green
        
        # Grant schema privileges
        Write-Host "Granting schema privileges..." -ForegroundColor Cyan
        $schemaSql = @"
GRANT ALL ON SCHEMA public TO $dbUser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $dbUser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $dbUser;
"@
        $schemaSqlFile = [System.IO.Path]::GetTempFileName() + ".sql"
        $schemaSql | Out-File -FilePath $schemaSqlFile -Encoding UTF8
        & $psqlPath -U $superUser -d $dbName -f $schemaSqlFile
        Remove-Item $schemaSqlFile -ErrorAction SilentlyContinue
        
        Write-Host ""
        Write-Host "[SUCCESS] Database setup complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Database connection details:" -ForegroundColor Cyan
        Write-Host "  Database: $dbName"
        Write-Host "  User: $dbUser"
        Write-Host "  Password: $dbPassword"
        Write-Host "  Host: localhost"
        Write-Host "  Port: 5432"
        Write-Host ""
        Write-Host "DATABASE_URL: postgresql://${dbUser}:${dbPassword}@localhost:5432/${dbName}" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[ERROR] Failed to create database. Check your password and try again." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Remove-Item $tempSqlFile -ErrorAction SilentlyContinue
}
