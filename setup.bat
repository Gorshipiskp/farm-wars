@echo off
cd /d "%~dp0"
echo One-time setup: Node.js (if needed), Python deps, web build, database.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
if errorlevel 1 pause
