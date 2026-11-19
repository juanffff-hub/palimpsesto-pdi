$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$palimpsestoPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $palimpsestoPython)) {
    $palimpsestoBundled = Get-ChildItem -LiteralPath 'C:\Program Files\WindowsApps' -Directory -Filter 'OpenAI.CodexPrimaryRuntime*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'dependencies\python\python.exe' } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($palimpsestoBundled -and (Test-Path -LiteralPath '..\..\work\pydeps')) { $palimpsestoPython = $palimpsestoBundled }
    else { $palimpsestoPython = (Get-Command python -ErrorAction Stop).Source }
}
Write-Host 'Abre http://127.0.0.1:8765 en tu navegador. Ctrl+C detiene el servidor.'
& $palimpsestoPython (Join-Path $PSScriptRoot 'run.py')
exit $LASTEXITCODE
