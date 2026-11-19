@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Instalar_Palimpsesto.ps1"
if errorlevel 1 pause
