from fastapi import APIRouter

from app.api.v1 import ai, auth, news, requests, sources, stats, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(requests.router)
api_router.include_router(ai.router)
api_router.include_router(news.router)
api_router.include_router(sources.router)
api_router.include_router(stats.router)
