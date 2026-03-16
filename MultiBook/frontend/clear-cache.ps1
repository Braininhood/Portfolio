# Clear Next.js build cache
# Run this if you're experiencing build errors or syntax errors

Write-Host "Clearing Next.js build cache..." -ForegroundColor Yellow

$pathsToRemove = @(
    ".next",
    "node_modules/.cache"
)

foreach ($path in $pathsToRemove) {
    if (Test-Path $path) {
        Write-Host "Removing $path..." -ForegroundColor Yellow
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Removed $path" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] $path does not exist" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[OK] Cache cleared! Restart your Next.js dev server." -ForegroundColor Green
Write-Host "Run: npm run dev" -ForegroundColor Cyan
