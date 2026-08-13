from fastapi import APIRouter

from app.api.v1.endpoints import favorite, history, news, users


api_router = APIRouter()
api_router.include_router(favorite.router)
api_router.include_router(history.router)
api_router.include_router(news.router)
api_router.include_router(users.router)
