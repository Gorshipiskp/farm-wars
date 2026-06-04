# Try to install Node.js LTS on Windows (winget or Chocolatey).
$ErrorActionPreference = "Stop"

function Refresh-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Test-NodeReady {
    return [bool](Get-Command node -ErrorAction SilentlyContinue) -and
        [bool](Get-Command npm -ErrorAction SilentlyContinue)
}

function Install-NodeViaWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        return $false
    }
    Write-Host "==> Installing Node.js LTS (winget)..." -ForegroundColor Yellow
    Write-Host "    UAC may ask for administrator permission."
    $proc = Start-Process -FilePath "winget" -ArgumentList @(
        "install", "-e", "--id", "OpenJS.NodeJS.LTS",
        "--accept-package-agreements", "--accept-source-agreements"
    ) -Wait -PassThru -NoNewWindow
    return $proc.ExitCode -eq 0
}

function Install-NodeViaChoco {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        return $false
    }
    Write-Host "==> Installing Node.js LTS (Chocolatey)..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath "choco" -ArgumentList @(
        "install", "nodejs-lts", "-y"
    ) -Wait -PassThru -NoNewWindow
    return $proc.ExitCode -eq 0
}

function Ensure-NodeInstalled {
    if (Test-NodeReady) {
        return $true
    }

    $ok = $false
    if (Install-NodeViaWinget) { $ok = $true }
    elseif (Install-NodeViaChoco) { $ok = $true }

    if (-not $ok) {
        Write-Host ""
        Write-Host "Could not install Node.js automatically." -ForegroundColor Red
        Write-Host "Options:"
        Write-Host "  1) Install manually: https://nodejs.org/ (LTS), then run play.bat again"
        Write-Host "  2) Use portable build (no Node to play): build-release.bat on a PC with Node,"
        Write-Host "     then run release\out\dist\FarmWars\Play-FarmWars.bat"
        return $false
    }

    Refresh-SessionPath
    if (-not (Test-NodeReady)) {
        Write-Host ""
        Write-Host "Node.js was installed but this terminal does not see it yet." -ForegroundColor Yellow
        Write-Host "Close PowerShell, open a new window, and run: .\play.bat"
        return $false
    }

    Write-Host ("==> Node " + (node -v) + ", npm " + (npm -v)) -ForegroundColor Green
    return $true
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not (Ensure-NodeInstalled)) { exit 1 }
}
