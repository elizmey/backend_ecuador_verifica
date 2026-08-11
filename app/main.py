from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend de VeriIA Ecuador: plataforma tecnológica contra la desinformación. "
        "Gestiona usuarios, análisis de noticias y textos, reportes ciudadanos, "
        "verificación de fuentes y comunicación con modelos de IA "
        "(NLP, Computer Vision y LLM para explicación de resultados).\n\n"
        "Usa el botón **Authorize** para autenticarte con OAuth2 (email + contraseña)."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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
        "worker_backend": settings.WORKER_BACKEND,
    }
