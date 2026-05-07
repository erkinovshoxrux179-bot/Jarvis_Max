param(
  [string]$PayloadSource = "..",
  [string]$OutDir = ".\\dist",
  [switch]$MakeInnoSetup
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
  $py = (Get-Command "python" -ErrorAction SilentlyContinue)
  if ($py) { return "python" }
  $pyLauncher = (Get-Command "py" -ErrorAction SilentlyContinue)
  if ($pyLauncher) { return "py -3.11" }
  throw "Python not found. Install Python 3.11+ and ensure 'python' or 'py' is available in PATH."
}

function Ensure-Dir([string]$p) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null }
}

Write-Host "== MARK XXXIX installer build ==" -ForegroundColor Cyan

Ensure-Dir $OutDir

$payloadDir = Join-Path $PSScriptRoot "payload"
if (Test-Path $payloadDir) { Remove-Item $payloadDir -Recurse -Force }
Ensure-Dir $payloadDir

Write-Host "Copying payload from $PayloadSource -> $payloadDir"
Copy-Item -Path (Join-Path $PSScriptRoot $PayloadSource "*") -Destination $payloadDir -Recurse -Force `
  -Exclude ".git",".venv","venv","__pycache__","dist","build",".pytest_cache",".mypy_cache",".idea",".vscode"

$PY = Resolve-Python
Write-Host "Using Python: $PY" -ForegroundColor Cyan

Write-Host "Installing PyInstaller (if needed)…"
Invoke-Expression "$PY -m pip install --upgrade pyinstaller" | Out-Null

Write-Host "Building installer wizard exe…"
Push-Location $PSScriptRoot
try {
  Invoke-Expression "$PY -m PyInstaller --noconfirm --clean --onefile --windowed --name MarkXXXIX-Setup --add-data `"payload;payload`" .\\installer_wizard.py"
} finally {
  Pop-Location
}

$exe = Join-Path $PSScriptRoot "dist\\MarkXXXIX-Setup.exe"
if (!(Test-Path $exe)) { throw "Build failed: $exe not found" }

Copy-Item $exe -Destination $OutDir -Force
Write-Host "EXE ready: $(Join-Path $OutDir 'MarkXXXIX-Setup.exe')" -ForegroundColor Green

if ($MakeInnoSetup) {
  $iss = Join-Path $PSScriptRoot "markxxxix.iss"
  if (!(Test-Path $iss)) { throw "Inno Setup script not found: $iss" }
  $iscc = (Get-Command "iscc.exe" -ErrorAction SilentlyContinue)
  if (!$iscc) {
    Write-Host "Inno Setup not found (iscc.exe). Skipping setup.exe packaging." -ForegroundColor Yellow
    exit 0
  }
  Write-Host "Packaging with Inno Setup…" -ForegroundColor Cyan
  & $iscc.Source $iss /O"$OutDir"
  Write-Host "Inno Setup output written to $OutDir" -ForegroundColor Green
}

