# Download TexasSolver console binary for Windows (AGPL).
# Run from poker_ai/:  .\scripts\install_texassolver.ps1
# Optional: .\scripts\install_texassolver.ps1 -Force

param(
    [switch]$Force,
    [string]$Version = "v0.2.0"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

$args = @("-m", "poker_ai", "solve", "install-texas", "--version", $Version)
if ($Force) { $args += "--force" }
& $py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
