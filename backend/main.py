from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.middleware import ApiResponseMiddleware


app = FastAPI(
    title="Toutiao News API",
    openapi_tags=[
        {"name": "news", "description": "News endpoints."},
        {"name": "users", "description": "User endpoints."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ApiResponseMiddleware)
app.include_router(api_router, prefix="/api")
