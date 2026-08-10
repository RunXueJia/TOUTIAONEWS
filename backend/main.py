from fastapi import FastAPI

from app.api.v1.router import api_router


app = FastAPI(
    title="Toutiao News API",
    openapi_tags=[
        {"name": "news", "description": "News endpoints."},
        {"name": "users", "description": "User endpoints."},
    ],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
