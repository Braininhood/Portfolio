# Long-running production playbook — logs under reports/playbook_logs/
$ErrorActionPreference = "Continue"
$Root = "D:\Poker AI\poker_ai"
$LogDir = Join-Path $Root "reports\playbook_logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Py = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location $Root

function Write-Log($name, $msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $msg" | Tee-Object -FilePath (Join-Path $LogDir $name) -Append
}

Write-Log "production_chain.log" "=== equity backfill (full) ==="
& $Py -m poker_ai equity backfill 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "equity_backfill.log") -Append
if ($LASTEXITCODE -ne 0) { Write-Log "production_chain.log" "equity backfill exit $LASTEXITCODE" }

foreach ($fmt in @("8max", "9max", "10max")) {
    Write-Log "production_chain.log" "=== solve preflop $fmt --production ==="
    & $Py -m poker_ai solve preflop --positions $fmt --production 2>&1 |
        Tee-Object -FilePath (Join-Path $LogDir "preflop_$fmt.log") -Append
    if ($LASTEXITCODE -ne 0) { Write-Log "production_chain.log" "preflop $fmt exit $LASTEXITCODE" }
}

Write-Log "production_chain.log" "=== production chain finished ==="
