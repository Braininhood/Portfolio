# Package Poker AI for Windows distribution (Phase W9 / Phase 12)
# Creates a portable ZIP installer. For MSIX, install Windows SDK + run with -Msix.
#
#   powershell -ExecutionPolicy Bypass -File poker_ai\scripts\package-msix.ps1
#   powershell -ExecutionPolicy Bypass -File poker_ai\scripts\package-msix.ps1 -Msix

param(
    [switch]$Msix,
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path (Join-Path $Root "poker_ai\pyproject.toml"))) {
    $Root = Split-Path $PSScriptRoot -Parent
}
$OutDir = Join-Path $Root "dist\poker-ai-$Version"
$ZipPath = Join-Path $Root "dist\poker-ai-$Version-win64.zip"

Write-Host "Poker AI packaging — version $Version"

& (Join-Path $Root "poker_ai\scripts\install.ps1") 2>$null
Push-Location (Join-Path $Root "apps\web")
try {
    if (-not (Test-Path "dist\index.html")) {
        npm run build
    }
} finally {
    Pop-Location
}

if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
New-Item -ItemType Directory -Path $OutDir | Out-Null

$Include = @("poker_ai", "apps\api", "apps\web\dist", "doc\README.md", "readme.md", "docker-compose.yml")
foreach ($item in $Include) {
    $src = Join-Path $Root $item
    if (Test-Path $src) {
        Copy-Item -Recurse -Force $src (Join-Path $OutDir (Split-Path $item -Leaf))
    }
}

@(
    "@echo off",
    "cd /d %~dp0poker_ai",
    "uv run python -m poker_ai serve --no-web",
    ""
) | Set-Content -Encoding ASCII (Join-Path $OutDir "Start-Poker-AI.bat")

New-Item -ItemType Directory -Force (Join-Path $Root "dist") | Out-Null
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path "$OutDir\*" -DestinationPath $ZipPath -Force
Write-Host "Created $ZipPath"

if ($Msix) {
    $MakeAppx = Get-Command makeappx.exe -ErrorAction SilentlyContinue
    if (-not $MakeAppx) {
        Write-Warning "makeappx.exe not found — install Windows SDK App Packaging Tools for MSIX."
        Write-Host "ZIP installer is ready at $ZipPath"
        exit 0
    }
    $MsixPath = Join-Path $Root "dist\poker-ai-$Version.msix"
    $Layout = Join-Path $Root "dist\msix-layout"
    if (Test-Path $Layout) { Remove-Item -Recurse -Force $Layout }
    New-Item -ItemType Directory -Path $Layout | Out-Null
    Copy-Item -Recurse -Force $OutDir\* $Layout
    & makeappx.exe pack /d $Layout /p $MsixPath /o
    Write-Host "Created $MsixPath"
}

Write-Host "Done. Run Start-Poker-AI.bat from extracted folder or: cd poker_ai && uv run python -m poker_ai serve"
