# Install PyTorch with CUDA for HHFormer training (Windows).
# RTX 50-series (5070 / 5070 Ti / …) uses Blackwell sm_120 — stable cu124 wheels often fail;
# use PyTorch nightly cu128: https://pytorch.org/get-started/locally/
#
# Usage (from poker_ai/):
#   .\scripts\install_torch_cuda.ps1          # skip if cu128 + CUDA already OK
#   .\scripts\install_torch_cuda.ps1 -Force   # reinstall (~2.8 GB download)

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $PackageRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Error "Create venv first: cd $PackageRoot; python -m venv .venv"
}

$IndexUrl = "https://download.pytorch.org/whl/nightly/cu128"

function Test-TorchCuda {
    param([string]$PythonExe)
    $check = @'
import sys
try:
    import torch
except OSError as e:
    print("import_error", e, file=sys.stderr)
    sys.exit(2)
ver = torch.__version__
cuda_built = torch.version.cuda or ""
ok = "+cu128" in ver and cuda_built.startswith("12.8") and torch.cuda.is_available()
print("ok" if ok else "bad", ver, cuda_built, torch.cuda.is_available())
sys.exit(0 if ok else 1)
'@
    $check | & $PythonExe - 2>&1 | Out-Null
    return $LASTEXITCODE -eq 0
}

Write-Host "Using: $Py"
& $Py --version

if (-not $Force -and (Test-TorchCuda $Py)) {
    Write-Host "PyTorch nightly cu128 with working CUDA is already installed. Use -Force to reinstall."
    & $Py -c "import torch; print('torch', torch.__version__); print('device', torch.cuda.get_device_name(0))"
    exit 0
}

Write-Host @"
Installing PyTorch nightly (CUDA 12.8).
First install downloads ~2.8 GB for torch alone; allow several minutes.
Do not interrupt — a partial install breaks 'import torch' until you re-run this script.
"@

# Upgrade in place; do not uninstall first (avoids broken half-installed torch).
$pipArgs = @(
    "-m", "pip", "install", "--upgrade", "--pre",
    "torch", "torchvision", "torchaudio",
    "--index-url", $IndexUrl
)
& $Py @pipArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed (exit $LASTEXITCODE). Re-run this script; do not use CPU-only 'pip install torch'."
}

Write-Host "Verifying CUDA..."
$verify = @'
import sys
import torch
print("torch", torch.__version__)
print("cuda built", torch.version.cuda)
print("is_available", torch.cuda.is_available())
if not torch.cuda.is_available():
    print("CUDA not available — update NVIDIA driver or re-run with -Force", file=sys.stderr)
    sys.exit(1)
x = torch.tensor([2.0], device="cuda")
print("smoke", x * x)
print("device", torch.cuda.get_device_name(0))
'@
$verify | & $Py -
if ($LASTEXITCODE -ne 0) {
    Write-Error "CUDA verification failed (exit $LASTEXITCODE)."
}
