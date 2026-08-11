from fastapi import APIRouter

from app.api.v1 import verify

api_router = APIRouter()
api_router.include_router(verify.router, prefix="/verify", tags=["Verificador"])
