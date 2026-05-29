# Build engine_core — MSVC or GCC (MinGW). Delegates to tools/build_engine.py
#
# Examples:
#   powershell -ExecutionPolicy Bypass -File tools/build_engine.ps1
#   powershell -ExecutionPolicy Bypass -File tools/build_engine.ps1 -Toolchain gcc
#   powershell -ExecutionPolicy Bypass -File tools/build_engine.ps1 -Toolchain msvc -Clean

param(
    [ValidateSet("auto", "msvc", "gcc")]
    [string]$Toolchain = "auto",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$args = @("tools/build_engine.py", "--toolchain", $Toolchain)
if ($Clean) { $args += "--clean" }

& py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
