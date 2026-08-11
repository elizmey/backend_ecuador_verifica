@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [ecverifica] Creando .env local con SQLite y proveedor IA mock...
  (
    echo ENV=development
    echo DEBUG=true
    echo SECRET_KEY=dev-only-change-me
    echo CORS_ORIGINS=*
    echo DATABASE_URL=sqlite:///./ecverifica.db
    echo UPLOAD_DIR=uploads
    echo AI_PROVIDER=mock
    echo AI_ENABLED=true
    echo WORKER_BACKEND=inline
    echo PORT=8000
  ) > .env
)

echo [ecverifica] Instalando dependencias de Python (usuario global, sin venv)...
py -m pip install --user -r requirements.txt
if errorlevel 1 (
  echo Error: no se pudieron instalar las dependencias. Instala Python 3.12+ desde python.org
  exit /b 1
)

echo [ecverifica] Iniciando en http://localhost:8000  (Swagger: /docs)
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
