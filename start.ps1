$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — please set UPSTREAM_API_KEY before using Cursor."
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing dependencies..."
& ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt

if ($env:PROXY_CONFIG) {
    Write-Host "Using config: $env:PROXY_CONFIG"
}
$py = ".venv\Scripts\python.exe"
$port = & $py -c "from src.config import load_settings; print(load_settings().port)"
Write-Host "Starting Cursor OpenAI Bridge on http://127.0.0.1:$port ..."
& $py -m uvicorn src.main:app --host 127.0.0.1 --port $port
