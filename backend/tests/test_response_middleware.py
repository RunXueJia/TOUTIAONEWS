from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.middleware import ApiResponseMiddleware
from main import app


def test_api_success_response_uses_code_200() -> None:
    client = TestClient(app)

    response = client.get("/api/users/get_user_list")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {"message": "Users router"},
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


def test_error_response_is_not_converted_to_a_success_response() -> None:
    test_app = FastAPI()
    test_app.add_middleware(ApiResponseMiddleware)

    @test_app.get("/api/failure")
    async def failure() -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": "invalid request"})

    response = TestClient(test_app).get("/api/failure")

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid request"}


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

    assert response.status_code == 404
    assert response.json() == {
        "code": 404,
        "message": "News 42 not found",
        "data": None,
    }
