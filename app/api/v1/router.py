from fastapi import APIRouter

from app.api.v1 import detect, verify

api_router = APIRouter()
api_router.include_router(verify.router, prefix="/verify", tags=["Verificador"])
api_router.include_router(detect.router, prefix="/detect", tags=["Detección de contenido sintético"])
