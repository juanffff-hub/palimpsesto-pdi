function Resolve-PalimpsestoPython {
    param([string]$ProjectRoot, [switch]$BasePython)
    $pythonPath = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    if (-not $BasePython -and (Test-Path -LiteralPath $pythonPath)) { return $pythonPath }
    $settingsPath = Join-Path $ProjectRoot 'local_settings.json'
    if (Test-Path -LiteralPath $settingsPath) {
        $settings = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($settings.python -and (Test-Path -LiteralPath $settings.python)) {
            if ($settings.dependencies -and (Test-Path -LiteralPath $settings.dependencies)) { $env:PYTHONPATH = $settings.dependencies }
            return $settings.python
        }
    }
    if ($env:PALIMPSESTO_PYTHON -and (Test-Path -LiteralPath $env:PALIMPSESTO_PYTHON)) { return $env:PALIMPSESTO_PYTHON }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidate = & py -3.12 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidate = & python -c 'import sys; print(sys.executable if sys.version_info[:2] == (3,12) else "")' 2>$null
        if ($LASTEXITCODE -eq 0 -and $candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    throw 'Instala Python 3.12 y sigue README.md, o configura PALIMPSESTO_PYTHON con su ruta.'
}
