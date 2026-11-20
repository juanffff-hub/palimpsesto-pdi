$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts\python_runtime.ps1')
$palimpsestoPython = Resolve-PalimpsestoPython -ProjectRoot $PSScriptRoot
Write-Host 'Abre http://127.0.0.1:8765 en tu navegador. Ctrl+C detiene el servidor.'
& $palimpsestoPython (Join-Path $PSScriptRoot 'run.py')
exit $LASTEXITCODE
