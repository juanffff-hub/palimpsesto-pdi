$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$palimpsestoPython = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $palimpsestoCandidate = & py -3.12 -c 'import sys; print(sys.executable)' 2>$null
    if ($LASTEXITCODE -eq 0) { $palimpsestoPython = $palimpsestoCandidate }
}
if (-not $palimpsestoPython) {
    $palimpsestoCandidate = Get-Command python -ErrorAction SilentlyContinue
    if ($palimpsestoCandidate) {
        $palimpsestoVersion = & $palimpsestoCandidate.Source -c 'import sys; print(sys.version_info[:2] == (3,12))' 2>$null
        if ($palimpsestoVersion -eq 'True') { $palimpsestoPython = $palimpsestoCandidate.Source }
    }
}
if (-not $palimpsestoPython) {
    throw 'Instala Python 3.12 o pide a Claude Code que localice un runtime 3.12 disponible. Consulta README.md. No se modificaron archivos del sistema.'
}
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
