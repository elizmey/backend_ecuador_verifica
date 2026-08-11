$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "[ecverifica] Creando .env local con proveedor IA mock..." -ForegroundColor Yellow
    @"
ENV=development
DEBUG=true
CORS_ORIGINS=*
AI_PROVIDER=mock
AI_ENABLED=true
PORT=3008
"@ | Set-Content -LiteralPath ".env" -Encoding UTF8
}

Write-Host "[ecverifica] Instalando dependencias de Python (usuario global, sin venv)..." -ForegroundColor Yellow
py -m pip install --user -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: no se pudieron instalar las dependencias. Instala Python 3.12+ desde python.org" -ForegroundColor Red
    exit 1
}

Write-Host "[ecverifica] Iniciando en http://localhost:3008  (Swagger: /docs)" -ForegroundColor Green
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3008

