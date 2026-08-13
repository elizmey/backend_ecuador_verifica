from fastapi import APIRouter

from app.api.v1 import adapt, chat, detect, verify

api_router = APIRouter()
api_router.include_router(verify.router, prefix="/verify", tags=["Verificador"])
api_router.include_router(detect.router, prefix="/detect", tags=["Detección de contenido sintético"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chatbot"])
api_router.include_router(adapt.router, prefix="/adapt", tags=["Adaptación para medios locales"])
