from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.middleware import ApiResponseMiddleware
from app.db.redis import close_redis_client, create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """在应用启动时校验 Redis 连接，并在关闭时释放连接池。"""
    redis_client = create_redis_client()
    try:
        await redis_client.ping()
        app.state.redis = redis_client
        yield
    finally:
        await close_redis_client(redis_client)


app = FastAPI(
    title="Toutiao News API",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "favorite", "description": "用户收藏相关接口；收藏状态查询支持匿名访问。"},
        {"name": "history", "description": "用户浏览历史模块。"},
        {"name": "news", "description": "新闻相关接口。"},
        {"name": "user", "description": "用户相关接口。"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiResponseMiddleware)
app.include_router(api_router, prefix="/api")
