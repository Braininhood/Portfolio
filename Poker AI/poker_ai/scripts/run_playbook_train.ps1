# Phase 7b — full-corpus multiway student (no row cap)
$ErrorActionPreference = "Continue"
$Root = "D:\Poker AI\poker_ai"
$LogDir = Join-Path $Root "reports\playbook_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Py = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location $Root

& $Py -m poker_ai train multiway-student --epochs 25 --row-limit 500000 --device cuda --batch-size 64 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "multiway_train.log") -Append
