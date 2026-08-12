from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.middleware import ApiResponseMiddleware


app = FastAPI(
    title="Toutiao News API",
    openapi_tags=[
        {"name": "favorite", "description": "用户收藏相关接口；收藏状态查询支持匿名访问。"},
        {"name": "news", "description": "新闻相关接口。"},
        {"name": "users", "description": "用户相关接口。"},
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
