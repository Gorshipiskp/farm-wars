# Build portable Farm Wars for Windows (release/out/dist/FarmWars/)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Farm Wars — release build"
Write-Host "    Root: $Root"

function Need-Cmd($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Command not found: $name"
    }
}

Need-Cmd py
Need-Cmd npm

Write-Host "==> Python deps (release)"
py -m pip install -q -r requirements-release.txt
py -m pip install -q pybind11 2>$null

Write-Host "==> SQLite database"
py tools/init_db.py --seed

Write-Host "==> C++ engine (optional)"
try {
    py tools/build_engine.py 2>$null
    Write-Host "    Engine: C++ module built"
} catch {
    Write-Host "    Engine: using Python stub (OK for play)"
}

Write-Host "==> Web client"
Set-Location web
if (-not (Test-Path node_modules)) { npm ci }
npm run build
Set-Location $Root

if (-not (Test-Path web/dist/index.html)) {
    throw "web/dist/index.html missing after build"
}

Write-Host "==> PyInstaller"
py -m PyInstaller release/farm_wars.spec --noconfirm --distpath release/out/dist --workpath release/out/build

$Out = Join-Path $Root "release/out/dist/FarmWars"
if (-not (Test-Path (Join-Path $Out "FarmWars.exe"))) {
    throw "FarmWars.exe not found in $Out"
}

New-Item -ItemType Directory -Force -Path (Join-Path $Out "data") | Out-Null

@'
@echo off
cd /d "%~dp0"
set FARM_WARS_PORTABLE=1
set FARM_WARS_OPEN_BROWSER=1
start "" "FarmWars.exe"
'@ | Set-Content -Encoding ASCII (Join-Path $Out "Play-FarmWars.bat")

@'
Farm Wars — portable build
==========================

1. Double-click Play-FarmWars.bat (or FarmWars.exe)
2. Browser opens at http://127.0.0.1:8765/
3. Create a match, share the join code on your LAN

Other PCs: http://YOUR_LAN_IP:8765/ (see console for IP)

Data folder: data/ next to this exe.
'@ | Set-Content -Encoding UTF8 (Join-Path $Out "README.txt")

Write-Host ""
Write-Host "=============================================="
Write-Host " DONE: $Out"
Write-Host " Run:  $Out\Play-FarmWars.bat"
Write-Host "=============================================="
