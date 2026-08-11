# VeriIA Ecuador — Backend (Verificador de desinformación)

API de **Verificación de desinformación en tiempo real** para **VeriIA Ecuador**.

> **Sin base de datos**: todo corre 100% en memoria. Nada se guarda ni se persiste.
> Ingresa una afirmación → análisis NLP + cruce con base de conocimiento y fuentes
> confiables → veredicto con explicación.

---

## Stack

| Capa | Tecnología |
|---|---|
| API | FastAPI + Uvicorn |
| Documentación | Swagger UI (`/docs`) + ReDoc (`/redoc`) |
| IA | Pluggable: `mock` (default) · `ollama` · `openai` · `google` |
| Almacenamiento | **En memoria** (no hay base de datos) |
| Tests | pytest + TestClient |
| Infraestructura | Docker / docker-compose |

---

## Estructura

```
BACKEND/
├── app/
│   ├── main.py                  # App FastAPI (CORS, /health, routers)
│   ├── core/config.py           # Configuración por variables de entorno
│   ├── data/knowledge.py        # Base de conocimiento EN MEMORIA (hechos + fuentes)
│   ├── schemas/verify.py        # Pydantic: request / response del verificador
│   ├── schemas/detect.py        # Pydantic: detección de contenido sintético
│   ├── api/v1/
│   │   ├── router.py            # Verificador + detección de imágenes
│   │   ├── verify.py            # Endpoints: /check, /verdicts, /sources, /known-claims
│   │   └── detect.py            # Endpoints: /image, /verdicts, /health
│   └── services/
│       ├── verifier.py          # Orquestación: NLP → hechos → fuentes → veredicto
│       ├── detection_service.py # Imagen → proveedor → clasificación → veredicto
│       └── ai/                  # Proveedores de IA (base, nlp, llm, vision, providers)
├── scripts/ensure-env.mjs       # Crea .env y verifica dependencias
├── tests/                       # pytest (health + verificador)
├── Dockerfile
├── docker-compose.yml
├── package.json                 # Comandos npm/pnpm
├── dev.bat / dev.ps1
└── requirements.txt
```

---

## Puesta en marcha (desarrollo local)

Requisitos: Python 3.12+ y Node.js (pnpm o npm). **No se usa venv ni base de datos.**

```powershell
pnpm install      # o npm install (instala dependencias de Python automáticamente)
pnpm run dev      # inicia en http://localhost:3008 con recarga automática
pnpm run start    # inicia sin recarga
```

Comandos disponibles (`pnpm run <script>`):

| Script | Descripción |
|---|---|
| `setup` | Instala las dependencias de Python (usuario global) |
| `dev` | Inicia uvicorn en el puerto **3008** con recarga |
| `start` | Inicia uvicorn en el puerto **3008** sin recarga |
| `test` | Ejecuta la suite de pytest |

Servidor: **http://localhost:3008** · Swagger: **http://localhost:3008/docs**

---

## Endpoints

### Verificador de desinformación

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/verify/check` | **Verifica una afirmación** (body: `{"claim": "..."}`) |
| GET | `/api/v1/verify/verdicts` | Lista los veredictos posibles |
| GET | `/api/v1/verify/sources` | Lista las fuentes confiables de referencia |
| GET | `/api/v1/verify/known-claims` | Lista las desinformaciones documentadas en memoria |
| GET | `/health` | Health check |

### Detección de contenido sintético (imágenes)

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/detect/image` | **Sube una imagen** y detecta manipulación/deepfake (multipart: `file` + opcional `claim`) |
| GET | `/api/v1/detect/verdicts` | Clasificaciones posibles de una imagen |
| GET | `/api/v1/detect/health` | Estado del proveedor de visión |

```bash
# Ejemplo de subida
curl -X POST http://localhost:3008/api/v1/detect/image \
  -F "file=@foto.png;type=image/png" \
  -F "claim=Imagen de un supuesto video"
```

**Respuesta** (resumen):

```json
{
  "filename": "foto.png",
  "verdict": "sospechosa",
  "verdict_label": "Sospechosa",
  "risk_score": 0.45,
  "manipulation_score": 0.4,
  "deepfake_score": 0.45,
  "ocr_text": "...",
  "objects": [{ "label": "person", "confidence": 0.93 }],
  "signals": ["bordes_inconsistentes"],
  "explanation": "...",
  "provider": "mock",
  "checked_at": "2026-08-11T00:00:00Z",
  "processing_ms": 12,
  "claim": "Imagen de un supuesto video"
}
```

**Clasificaciones**: `autentica` (riesgo < 0.3) · `sospechosa` (0.3–0.6) · `manipulada` (≥ 0.6). El archivo se procesa en memoria y **se elimina al terminar** — nada se persiste.

El proveedor `mock` calcula los scores a partir del contenido del archivo, por lo que cada imagen produce un resultado distinto y determinista (ideal para desarrollo y demo).

### Ejemplo — `POST /api/v1/verify/check`

```json
// Request
{ "claim": "Las vacunas causan autismo" }

// Response (resumen)
{
  "claim": "Las vacunas causan autismo",
  "verdict": "falso",
  "verdict_label": "Falso",
  "confidence": 0.97,
  "explanation": "Estudios científicos internacionales...",
  "checked_at": "2026-08-11T00:00:00Z",
  "nlp": { "language": "es", "sentiment": "...", "claims": [], "entities": [], "topics": [] },
  "source_matches": [],
  "evidence": {
    "fact_used": "vacunas-autismo",
    "fact_category": "salud",
    "negation_detected": false,
    "recommended_sources": [ { "name": "...", "url": "...", "category": "oficial" } ]
  }
}
```

El verificador también entiende negaciones: `"Las vacunas no causan autismo"` devuelve `verdadero`.

---

## Veredictos

| Código | Etiqueta | Cuándo |
|---|---|---|
| `verdadero` | Verdadero | Coincide con un hecho documentado (o niega una desinformación) |
| `falso` | Falso | Coincide con una desinformación documentada |
| `enganyoso` | Engañoso | Detecta lenguaje manipulativo o mezcla de datos sin contexto |
| `sin_evidencia` | Sin evidencia suficiente | No hay coincidencia con casos documentados |

---

## Modelos de IA

La capa de IA es **pluggable** vía `AI_PROVIDER` en `.env`:

| Proveedor | Descripción | Requisitos |
|---|---|---|
| `mock` *(default)* | Respuestas deterministas para desarrollo/tests | Ninguno |
| `ollama` | Modelos locales | Ollama corriendo en `OLLAMA_BASE_URL` |
| `openai` | OpenAI o compatible (OpenRouter, Azure, etc.) | `OPENAI_API_KEY` |
| `google` | Gemini (Google AI) | `GOOGLE_AI_API_KEY` |

El NLP alimenta el análisis (claims, sentimiento, entidades, temas, señales de
manipulación); el veredicto final lo determina la base de conocimiento en memoria.

---

## Docker

```bash
docker compose up --build -d
```

Levanta solo la API en el puerto **3008**. Sin PostgreSQL, sin Redis, sin base de datos.

---

## Tests

```bash
pnpm run test
```

Cubren: health/Swagger, verificación de afirmaciones falsas/verdaderas/engañosas,
negaciones, afirmaciones desconocidas, cruce de fuentes, y detección de imágenes
(subida válida, extensiones inválidas, clasificaciones y limpieza de archivos temporales).

---

## Conexión con el frontend

- **Base URL**: `http://localhost:3008`
- **Prefijo API**: `/api/v1`
- **CORS**: abierto por defecto (`CORS_ORIGINS=*`) — el frontend puede llamar desde cualquier origen.
