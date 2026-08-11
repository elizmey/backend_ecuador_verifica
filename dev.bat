@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [ecverifica] Creando .env local con proveedor IA mock...
  (
    echo ENV=development
    echo DEBUG=true
    echo CORS_ORIGINS=*
    echo AI_PROVIDER=mock
    echo AI_ENABLED=true
    echo PORT=3008
  ) > .env
)

echo [ecverifica] Instalando dependencias de Python (usuario global, sin venv)...
py -m pip install --user -r requirements.txt
if errorlevel 1 (
  echo Error: no se pudieron instalar las dependencias. Instala Python 3.12+ desde python.org
  exit /b 1
)

echo [ecverifica] Iniciando en http://localhost:3008  (Swagger: /docs)
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3008

