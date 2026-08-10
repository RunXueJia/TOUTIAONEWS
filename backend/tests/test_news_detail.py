from datetime import datetime

from fastapi.testclient import TestClient

from app.db.database import get_db
from main import app


class _FakeNews:
    id = 1
    publish_time = datetime(2024, 1, 1, 8, 0)
    created_at = datetime(2026, 8, 10, 12, 0)
    updated_at = datetime(2026, 8, 10, 12, 0)
    title = "测试新闻"
    description = "简介"
    content = "正文"
    image = None
    author = "作者"
    category_id = 1
    views = 10


class _FakeSession:
    async def get(self, model, news_id):
        return _FakeNews() if news_id == 1 else None


def test_get_news_detail_returns_article():
    session = _FakeSession()

    async def fake_db():
        yield session

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/news/detai?id=1")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["id"] == 1
    assert payload["data"]["content"] == "正文"


def test_get_news_detail_returns_not_found():
    session = _FakeSession()

    async def fake_db():
        yield session

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/news/detai?id=999")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 404


def test_get_news_detail_requires_positive_id():
    response = TestClient(app).get("/api/news/detai?id=0")
    assert response.status_code == 422
