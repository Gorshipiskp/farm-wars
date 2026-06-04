# Run Farm Wars from source (Windows PowerShell): server + web UI in browser.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Farm Wars - play from source" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' not found. Install Python 3.11+ from python.org"
}

if (-not (Test-Path "db\farm_wars.db")) {
    Write-Host "==> Creating database"
    py tools\init_db.py --seed
}

$distIndex = "web\dist\index.html"
if (-not (Test-Path $distIndex)) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "web\dist missing. Install Node.js, then: cd web; npm ci; npm run build"
    }
    Write-Host "==> Building web client (first time)"
    Push-Location web
    if (-not (Test-Path node_modules)) { npm ci }
    npm run build
    Pop-Location
}

$env:FARM_WARS_OPEN_BROWSER = "1"
if (-not $env:FARM_WARS_HOST) { $env:FARM_WARS_HOST = "0.0.0.0" }
if (-not $env:FARM_WARS_PORT) { $env:FARM_WARS_PORT = "8765" }

$localUrl = "http://127.0.0.1:" + $env:FARM_WARS_PORT + "/"
Write-Host "==> Starting server (Ctrl+C to stop)"
Write-Host ("    Local: " + $localUrl)
py -m server
