from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend de VeriIA Ecuador — Verificador de desinformación en tiempo real. "
        "Ingresa una afirmación y obtén análisis NLP, cruce con fuentes confiables y "
        "un veredicto con explicación. **100% en memoria: no se guarda nada, no usa "
        "base de datos.**\n\n"
        "Endpoint principal: `POST /api/v1/verify/check`"
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_origins_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Sistema"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "veriia-ecuador-backend",
        "version": settings.APP_VERSION,
        "env": settings.ENV,
        "ai_provider": settings.AI_PROVIDER,
        "storage": "memory",
    }
