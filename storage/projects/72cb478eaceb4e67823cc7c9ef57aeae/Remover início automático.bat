@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Gerenciar início automático.ps1" -Action Remove
if errorlevel 1 pause
