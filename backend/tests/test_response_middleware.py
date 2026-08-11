from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.middleware import ApiResponseMiddleware
from main import app


def test_api_success_response_uses_code_200() -> None:
    test_app = FastAPI()
    test_app.add_middleware(ApiResponseMiddleware)

    @test_app.get("/api/success")
    async def success() -> dict[str, str]:
        """提供未包装的成功响应，用于验证中间件。"""
        return {"message": "success"}

    client = TestClient(test_app)

    response = client.get("/api/success")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {"message": "success"},
    }


def test_standard_response_is_not_wrapped_twice() -> None:
    test_app = FastAPI()
    test_app.add_middleware(ApiResponseMiddleware)

    @test_app.get("/api/already_standard")
    async def already_standard() -> dict[str, object]:
        return {"code": 200, "message": "created", "data": {"id": 1}}

    response = TestClient(test_app).get("/api/already_standard")

    assert response.status_code == 200
    assert response.json() == {"code": 200, "message": "created", "data": {"id": 1}}


def test_error_response_is_returned_in_standard_body() -> None:
    test_app = FastAPI()
    test_app.add_middleware(ApiResponseMiddleware)

    @test_app.get("/api/failure")
    async def failure() -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": "invalid request"})

    response = TestClient(test_app).get("/api/failure")

    assert response.status_code == 200
    assert response.json() == {
        "code": 400,
        "message": "invalid request",
        "data": None,
    }


def test_missing_api_route_uses_code_404() -> None:
    test_app = FastAPI()
    test_app.add_middleware(ApiResponseMiddleware)

    response = TestClient(test_app).get("/api/missing")

    assert response.status_code == 200
    assert response.json() == {"code": 404, "message": "Not Found", "data": None}


def test_missing_api_data_uses_code_404() -> None:
    test_app = FastAPI()
    test_app.add_middleware(ApiResponseMiddleware)

    @test_app.get("/api/news/{news_id}")
    async def get_news(news_id: int) -> None:
        raise HTTPException(status_code=404, detail=f"News {news_id} not found")

    response = TestClient(test_app).get("/api/news/42")

    assert response.status_code == 200
    assert response.json() == {
        "code": 404,
        "message": "News 42 not found",
        "data": None,
    }
