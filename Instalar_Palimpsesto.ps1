$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts\python_runtime.ps1')
$palimpsestoPython = Resolve-PalimpsestoPython -ProjectRoot $PSScriptRoot -BasePython
$palimpsestoVenv = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $palimpsestoVenv)) {
    & $palimpsestoPython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual.' }
}
& $palimpsestoVenv -m pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) { throw 'Fallo al instalar PyTorch CPU. Comprueba la conexion y vuelve a intentar.' }
& $palimpsestoVenv -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Fallo al instalar dependencias. Conserva el mensaje y consulta README.md.' }
& $palimpsestoVenv -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Hay dependencias incompatibles; revisa el resultado antes de continuar.' }
& $palimpsestoVenv scripts/check.py
if ($LASTEXITCODE -ne 0) { throw 'La verificacion detecto un fallo. No declarar la instalacion validada.' }
Write-Host 'Instalacion y pruebas completadas. Ejecuta Iniciar_Palimpsesto.cmd.'
