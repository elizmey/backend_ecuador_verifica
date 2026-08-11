# VeriIA Ecuador — Backend

Backend de la plataforma de verificación de contenidos **VeriIA Ecuador** (anti-desinformación).
API REST construida con **Python + FastAPI**, escalable con **Docker**, documentada con **Swagger** y conectada a modelos de **IA** (NLP, Computer Vision y LLM).

> Estructura inspirada en el backend de Orion (`stats-service`). El código de Orion no se toca.

---

## Stack

| Capa | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Documentación | Swagger UI (`/docs`) + ReDoc (`/redoc`) |
| Base de datos | PostgreSQL 16 (SQLAlchemy 2 + psycopg3) |
| Autenticación | OAuth2 Password flow + JWT (bcrypt para hashing) |
| Tareas asíncronas | Celery + Redis (modo `inline` para desarrollo) |
| Migraciones | Alembic |
| Tests | pytest + TestClient |
| Infraestructura | Docker / docker-compose |

---

## Estructura del proyecto

```
BACKEND/
├── app/
│   ├── main.py                  # App FastAPI (CORS, routers, lifespan)
│   ├── core/                    # config, database, security (JWT/bcrypt), deps
│   ├── models/                  # ORM: User, VerificationRequest, AnalysisResult, NewsArticle, Source
│   ├── schemas/                 # Pydantic: auth, user, request, analysis, news, source, stats
│   ├── api/v1/                  # Routers: auth, users, requests, ai, news, sources, stats
│   ├── services/
│   │   ├── user_service.py
│   │   ├── request_service.py   # CRUD + dispatch de procesamiento
│   │   ├── news_service.py      # Noticias + vinculación con solicitudes
│   │   ├── source_verification.py  # Cruzado de texto contra fuentes confiables
│   │   ├── stats_service.py     # Agregados para el dashboard
│   │   ├── storage.py           # Upload de imágenes
│   │   └── ai/
│   │       ├── base.py          # Contrato de proveedores de IA
│   │       ├── provider_factory.py
│   │       ├── providers/       # mock | ollama | openai | google
│   │       ├── nlp.py           # Análisis de texto
│   │       ├── vision.py        # Computer Vision
│   │       ├── llm.py           # Explicación de resultados
│   │       └── pipeline.py      # Orquestación NLP → Fuentes → Vision → LLM
│   └── workers/                 # Celery app + tareas
├── migrations/                  # Alembic (env.py + script.py.mako)
├── scripts/                     # Utilidades (ensure-env.mjs)
├── tests/                       # pytest (health, auth, requests, ai)
├── Dockerfile
├── docker-compose.yml
├── package.json                 # Comandos npm/pnpm: dev, start, test
├── dev.bat / dev.ps1            # Desarrollo local (Windows)
├── alembic.ini
└── requirements.txt
```

---

## Puesta en marcha rápida (desarrollo local)

Requisitos: Python 3.12+ y Node.js (pnpm o npm). **No se usa venv**: las dependencias de Python se instalan en el entorno de usuario (`py -m pip install --user`).

**Windows:**
```powershell
pnpm install      # o npm install (instala dependencias de Python automáticamente)
pnpm run dev      # inicia con recarga automática (--reload)
pnpm run start    # inicia sin recarga
```

Los scripts `dev`/`start` generan automáticamente un `.env` con SQLite + proveedor IA `mock` para que funcione sin Docker ni modelos.

Servidor: **http://localhost:8000** · Swagger: **http://localhost:8000/docs**

Comandos disponibles (`pnpm run <script>`):

| Script | Descripción |
|---|---|
| `setup` | Instala las dependencias de Python (usuario global) |
| `dev` | Inicia uvicorn con recarga automática |
| `start` | Inicia uvicorn sin recarga |
| `test` | Ejecuta la suite de pytest |
| `migrate:upgrade` / `migrate:make` | Aplica / genera migraciones de Alembic |

> Si ya tienes PostgreSQL corriendo, edita `.env` y usa `DATABASE_URL=postgresql+psycopg://usuario:pass@localhost:5432/veriia`. Las tablas se crean automáticamente al arrancar (para producción usa Alembic, ver abajo).

---

## Docker (producción / escalable)

```bash
docker compose up --build -d
```

Levanta:
- `postgres` (PostgreSQL 16) con volumen persistente
- `redis` (broker de tareas)
- `backend` (API FastAPI, puerto **8000**)
- `worker` (Celery para procesamiento IA asíncrono)

Para usar el procesamiento asíncrono con Celery:
```bash
WORKER_BACKEND=celery docker compose up --build -d
```

El API **por defecto** procesa en línea (modo `inline`, hilo interno); en producción recomienda `WORKER_BACKEND=celery` y escalar el worker.

---

## Documentación (Swagger)

- **Swagger UI**: `GET /docs`
- **ReDoc**: `GET /redoc`
- **OpenAPI JSON**: `GET /openapi.json`

Para probar los endpoints autenticados usa el botón **Authorize** con email + contraseña (OAuth2 password flow).

---

## Roles y permisos

| Rol | Permisos |
|---|---|
| `user` | Crear/ver/eliminar **sus** solicitudes y noticias, ejecutar el pipeline, usar endpoints de IA y consultar fuentes |
| `verifier` | Todo lo de `user` + fijar veredicto final de cualquier solicitud + estadísticas del dashboard |
| `admin` | Todo lo de `verifier` + gestión de usuarios y de fuentes confiables (crear/editar/eliminar) |

El primer admin se crea con el script de seed:
```bash
py -m app.scripts.seed_admin
```
Usa `ADMIN_EMAIL`, `ADMIN_FULL_NAME` y `ADMIN_PASSWORD` de `.env`. También puedes crearlo manualmente:
```python
from app.core.database import SessionLocal
from app.services.user_service import create_user
from app.models.user import UserRole
db = SessionLocal()
create_user(db, "admin@veriia.ec", "Administrador", "password123", role=UserRole.admin)
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/auth/register` | Registrar usuario |
| POST | `/api/v1/auth/login` | Iniciar sesión (OAuth2) |
| GET | `/api/v1/auth/me` | Usuario actual |
| GET/PATCH/DELETE | `/api/v1/users` | Gestión de usuarios (admin) |
| POST | `/api/v1/requests` | Crear solicitud (form-data: `claim` + imágenes) |
| GET | `/api/v1/requests` | Listar solicitudes |
| GET | `/api/v1/requests/{id}` | Detalle con análisis |
| POST | `/api/v1/requests/{id}/process` | Ejecutar pipeline IA |
| POST | `/api/v1/requests/{id}/verdict` | Fijar veredicto (verifier/admin) |
| POST | `/api/v1/news` | Registrar una noticia |
| GET | `/api/v1/news` | Listar noticias |
| GET | `/api/v1/news/{id}` | Detalle con solicitudes vinculadas |
| POST | `/api/v1/news/{id}/process` | Analizar la noticia (crea solicitud vinculada) |
| GET | `/api/v1/sources` | Listar fuentes confiables |
| POST/PATCH/DELETE | `/api/v1/sources` | Gestión de fuentes (admin) |
| GET | `/api/v1/sources/match/text?text=...` | Cruzar texto contra fuentes |
| GET | `/api/v1/stats/overview` | Resumen del dashboard (verifier/admin) |
| GET | `/api/v1/stats/trends?days=30` | Tendencia de solicitudes por día |
| GET | `/api/v1/stats/top-sources` | Fuentes más referenciadas |
| POST | `/api/v1/ai/nlp` | Análisis NLP de texto |
| POST | `/api/v1/ai/vision` | Análisis de imagen (CV) |
| POST | `/api/v1/ai/explain` | Explicación LLM |
| GET | `/api/v1/ai/health` | Estado del proveedor IA |
| GET | `/health` | Health check |

---

## Modelos de IA

La capa de IA es **pluggable** vía `AI_PROVIDER` en `.env`:

| Proveedor | Descripción | Requisitos |
|---|---|---|
| `mock` *(default)* | Respuestas deterministas para desarrollo/tests | Ninguno |
| `ollama` | Modelos locales (NLP, visión con `llava`, LLM) | Ollama corriendo en `OLLAMA_BASE_URL` |
| `openai` | OpenAI o compatible (OpenRouter, Azure, etc.) | `OPENAI_API_KEY` |
| `google` | Gemini (Google AI) | `GOOGLE_AI_API_KEY` + `AI_PROVIDER=google` |

Flujo del pipeline de una solicitud (`POST /requests/{id}/process`):

1. **NLP** → analiza el texto de la afirmación (claims, sentimiento, entidades, temas, señales de manipulación).
2. **Fuentes** → cruza el texto contra las fuentes confiables (`sources`) y guarda `source_references`.
3. **Computer Vision** → analiza cada imagen (score de manipulación, deepfake, OCR, objetos).
4. **LLM** → genera una explicación en lenguaje natural + veredicto recomendado + confianza, considerando las fuentes encontradas.

Cada etapa se guarda en `analysis_results` y la solicitud queda con estado `completed`/`failed`.

---

## Tests

```bash
pnpm run test
```

Cubren: health/Swagger, registro y login, CRUD de solicitudes, permisos por rol, pipeline completo (NLP+Vision+LLM) y endpoints de IA (con proveedor mock).

---

## Migraciones (Alembic)

El arranque crea las tablas automáticamente (ideal para dev). Para gestión de esquema en producción:

```bash
# Generar una migración nueva a partir de los modelos
pnpm run migrate:make -- "descripcion"

# Aplicar migraciones
pnpm run migrate:upgrade
```

`migrations/env.py` ya carga la URL de `app.core.config` (no depende de `.env` manual).

---

## Escalabilidad

- **API stateless** → múltiples workers de uvicorn o réplicas detrás de un balanceador.
- **Tareas asíncronas** → Celery + Redis; el worker se escala independientemente (p.ej. `--concurrency` o varias réplicas).
- **Proveedores de IA** → abstraídos; cambiar de modelo local a nube solo requiere variables de entorno.
- **Volúmenes** → `uploads` (imágenes) y `logs` compartidos entre API y worker en Docker.
