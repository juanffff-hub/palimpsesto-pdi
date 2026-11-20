@echo off
if not exist "%~dp0.public_runtime" mkdir "%~dp0.public_runtime"
echo detener>"%~dp0.public_runtime\stop.request"
echo Se solicito detener la demo y cerrar el enlace publico.
pause
