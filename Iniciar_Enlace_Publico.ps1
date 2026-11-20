$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts\python_runtime.ps1')
$palimpsestoPython = Resolve-PalimpsestoPython -ProjectRoot $PSScriptRoot
& $palimpsestoPython -c 'import waitress'
if ($LASTEXITCODE -ne 0) {
    & $palimpsestoPython -m pip install waitress==3.0.2
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar el servidor de la demo.' }
}
$env:PYTHONIOENCODING = 'utf-8'
Write-Host 'Demo gratuita. Mantén este computador encendido y conectado. Ctrl+C para detener.'
& $palimpsestoPython -u (Join-Path $PSScriptRoot 'scripts\share_public.py')
exit $LASTEXITCODE
