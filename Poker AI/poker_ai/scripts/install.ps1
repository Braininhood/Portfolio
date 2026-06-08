# Poker AI — Windows bootstrap (Phase W9 / Phase 12)
# Run from repo root:  powershell -ExecutionPolicy Bypass -File poker_ai\scripts\install.ps1
# Linux / macOS:       ./poker_ai/scripts/install.sh   (or ./scripts/install.sh)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $Root "poker_ai\pyproject.toml"))) {
    $Root = Split-Path $PSScriptRoot -Parent
}
$PokerAi = Join-Path $Root "poker_ai"
$Web = Join-Path $Root "apps\web"

Write-Host "Poker AI install — repo: $Root"

# 1. Python 3.11+
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Python not found. Install Python 3.11+ and add to PATH."
}
$ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $ver.Split(".")
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) {
    Write-Error "Python 3.11+ required (found $ver)."
}
Write-Host "Python $ver OK"

# 2. uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv…"
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv not available after install."
}

# 3. Sync poker_ai + API extras
Push-Location $PokerAi
try {
    Write-Host "Syncing dependencies (uv sync --all-extras)…"
    uv sync --all-extras
} finally {
    Pop-Location
}

# 4. Build web (same-origin API — no /api prefix)
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "npm not found. Install Node.js 18+ for the dashboard build."
}
Push-Location $Web
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "npm install…"
        npm install
    }
    $env:VITE_API_BASE_URL = ""
    $env:VITE_WS_BASE_URL = "ws://127.0.0.1:8000"
    Write-Host "npm run build…"
    npm run build
} finally {
    Pop-Location
}

# 5. Migrations
Push-Location $PokerAi
try {
    Write-Host "Database migrate…"
    uv run python -m poker_ai db migrate
} finally {
    Pop-Location
}

# 6. Start API (serves apps/web/dist when present)
Write-Host "Starting server (API + static dashboard)…"
Push-Location $PokerAi
try {
    Start-Process -FilePath "uv" -ArgumentList @(
        "run", "python", "-m", "poker_ai", "serve", "--no-web", "--no-reload"
    ) -WorkingDirectory $PokerAi
} finally {
    Pop-Location
}

Write-Host "Done. Browser should open at http://127.0.0.1:8000/status when the API is ready."
Write-Host "Leave the new terminal window running, or run: cd poker_ai && uv run python -m poker_ai serve --no-web"
