$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:BIL372_USER_STORE = 'memory'

$localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $localPython) {
    & $localPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
} else {
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
}
