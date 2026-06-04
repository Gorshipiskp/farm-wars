# One-time Windows setup: Node (optional auto), pip, DB seed, web build.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

. (Join-Path $Root "scripts\install-node.ps1")

Write-Host "==> Farm Wars - one-time setup" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Install Python 3.11+ from https://www.python.org/downloads/ (check Add to PATH)"
}

if (-not (Test-NodeReady)) {
    if (-not (Ensure-NodeInstalled)) { exit 1 }
}

Write-Host "==> Python packages"
py -m pip install -q -r client\requirements.txt

Write-Host "==> Database"
py tools\init_db.py --seed

Write-Host "==> Web client"
Push-Location web
if (-not (Test-Path node_modules)) { npm ci }
npm run build
Pop-Location

Write-Host ""
Write-Host "Setup done. Run the game with: .\play.bat" -ForegroundColor Green
