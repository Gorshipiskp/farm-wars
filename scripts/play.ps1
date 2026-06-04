# Run Farm Wars from source (Windows PowerShell): server + web UI in browser.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

. (Join-Path $Root "scripts\install-node.ps1")

Write-Host "==> Farm Wars - play from source" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' not found. Install Python 3.11+ from https://www.python.org/downloads/"
}

if (-not (Test-Path "db\farm_wars.db")) {
    Write-Host "==> Creating database"
    py tools\init_db.py --seed
}

$distIndex = "web\dist\index.html"
if (-not (Test-Path $distIndex)) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Host "==> Node.js not found (needed once to build the web client)"
        if (-not (Ensure-NodeInstalled)) {
            exit 1
        }
    }
    Write-Host "==> Building web client (first time, may take 1-2 min)"
    Push-Location web
    if (-not (Test-Path node_modules)) { npm ci }
    npm run build
    Pop-Location
    if (-not (Test-Path $distIndex)) {
        throw "web build failed: $distIndex still missing"
    }
}

$env:FARM_WARS_OPEN_BROWSER = "1"
if (-not $env:FARM_WARS_HOST) { $env:FARM_WARS_HOST = "0.0.0.0" }
if (-not $env:FARM_WARS_PORT) { $env:FARM_WARS_PORT = "8765" }

$localUrl = "http://127.0.0.1:" + $env:FARM_WARS_PORT + "/"
Write-Host "==> Starting server (Ctrl+C to stop)"
Write-Host ("    Local: " + $localUrl)
py -m server
