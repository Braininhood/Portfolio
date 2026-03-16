# Kill all processes listening on ports 8080 and 8081 (e.g. dev servers)
# Run: .\scripts\kill-ports.ps1   or   powershell -ExecutionPolicy Bypass -File .\scripts\kill-ports.ps1

$ports = @(8080, 8081)
foreach ($port in $ports) {
  $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  if ($conn) {
    $pids = $conn.OwningProcess | Sort-Object -Unique
    foreach ($pid in $pids) {
      Write-Host "Killing process $pid on port $port"
      Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
  } else {
    Write-Host "No process found on port $port"
  }
}
Write-Host "Done."
