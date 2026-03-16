# Migrate all data from local DB to Supabase (PostgreSQL).
# Source: LOCAL_DATABASE_URL in .env (local Postgres) OR backend/db.sqlite3 (SQLite).
# Target: DATABASE_URL in .env (Supabase).
# Prerequisites: DATABASE_URL pointing to Supabase; Supabase schema exists (run migrate --settings=config.settings.development).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$backupFile = Join-Path $PSScriptRoot "data_backup.json"
$envFile = Join-Path $PSScriptRoot ".env"

# Check for LOCAL_DATABASE_URL (optional) - if set, dump from local Postgres; else from SQLite
$useLocalPg = $false
if (Test-Path $envFile) {
    $line = Get-Content $envFile | Where-Object { $_ -match '^\s*LOCAL_DATABASE_URL\s*=' -and $_ -notmatch '^\s*#' } | Select-Object -First 1
    if ($line -and $line -match '=\s*(.+)') {
        $val = $Matches[1].Trim()
        if ($val -and $val.StartsWith('postgresql://')) { $useLocalPg = $true }
    }
}

if (-not (Test-Path $venvPython)) {
    Write-Error "Venv not found. Run: python -m venv venv; .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

if (-not $useLocalPg) {
    if (-not (Test-Path (Join-Path $PSScriptRoot "db.sqlite3"))) {
        Write-Warning "backend/db.sqlite3 not found and LOCAL_DATABASE_URL not set. For local Postgres: set LOCAL_DATABASE_URL=postgresql://user:pass@host:5432/dbname in .env. For SQLite: put your DB at backend/db.sqlite3."
        exit 1
    }
}

Write-Host "Ensure backend/.env has DATABASE_URL pointing to Supabase (for the load step)." -ForegroundColor Gray

if ($useLocalPg) {
    Write-Host "Source: local PostgreSQL (LOCAL_DATABASE_URL)" -ForegroundColor Cyan
    Write-Host "Step 1/2: Dumping data from local PostgreSQL..." -ForegroundColor Cyan
    & $venvPython manage.py dumpdata `
        --settings=config.settings.local_pg_for_dump `
        --natural-foreign `
        --natural-primary `
        -e contenttypes `
        -e auth.Permission `
        -o $backupFile `
        --indent 2
} else {
    Write-Host "Source: local SQLite (db.sqlite3)" -ForegroundColor Cyan
    Write-Host "Step 0/3: Ensuring local SQLite has schema (migrate)..." -ForegroundColor Cyan
    & $venvPython manage.py migrate --settings=config.settings.sqlite_for_dump
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Local migrate failed."
        exit $LASTEXITCODE
    }
    Write-Host "Step 1/3: Dumping data from local SQLite (db.sqlite3)..." -ForegroundColor Cyan
    & $venvPython manage.py dumpdata `
        --settings=config.settings.sqlite_for_dump `
        --natural-foreign `
        --natural-primary `
        -e contenttypes `
        -e auth.Permission `
        -o $backupFile `
        --indent 2
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "dumpdata failed."
    exit $LASTEXITCODE
}

if ($useLocalPg) {
    Write-Host "Step 2/2: Loading data into Supabase (from .env DATABASE_URL)..." -ForegroundColor Cyan
} else {
    Write-Host "Step 2/3: Loading data into Supabase (from .env DATABASE_URL)..." -ForegroundColor Cyan
}
& $venvPython manage.py loaddata $backupFile --settings=config.settings.development

if ($LASTEXITCODE -ne 0) {
    Write-Error "loaddata failed. Fix errors above (e.g. duplicate keys, missing FKs) then run: .\venv\Scripts\python.exe manage.py loaddata data_backup.json --settings=config.settings.development"
    exit $LASTEXITCODE
}

if (-not $useLocalPg) {
    Write-Host "Step 3/3: Done." -ForegroundColor Green
} else {
    Write-Host "Done." -ForegroundColor Green
}
Write-Host "All data migrated to Supabase. Backup kept: $backupFile (you can delete it after verifying.)"
