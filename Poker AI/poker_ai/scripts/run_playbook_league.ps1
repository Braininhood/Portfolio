# Phase 9 — 6h wall-clock league (logs under reports/playbook_logs/)
$ErrorActionPreference = "Continue"
$Root = "D:\Poker AI\poker_ai"
$LogDir = Join-Path $Root "reports\playbook_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Py = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location $Root

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$ts] league run --until-hours 6 starting" | Out-File (Join-Path $LogDir "league_6h.log") -Append

& $Py -m poker_ai league run --until-hours 6 --hands-per-matchup 200 --workers 16 --until-hu --table-sizes hu,6max,9max 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "league_6h.log") -Append

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$ts] league finished exit=$LASTEXITCODE" | Out-File (Join-Path $LogDir "league_6h.log") -Append
