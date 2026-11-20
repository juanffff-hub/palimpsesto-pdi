@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Iniciar_Enlace_Publico.ps1"
pause
