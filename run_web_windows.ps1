$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = Join-Path $ProjectRoot "src"

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python wurde nicht gefunden. Bitte ein neues Terminal öffnen oder Python 3 installieren."
}

Push-Location $ProjectRoot
try {
    Write-Host "SP_Naka startet auf http://127.0.0.1:8765/calculation"
    Write-Host "Zum Beenden Strg+C drücken."
    & $Python.Source -m sp_naka.webapp
}
finally {
    Pop-Location
}
