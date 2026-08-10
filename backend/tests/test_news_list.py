from datetime import datetime

from fastapi.testclient import TestClient

from app.api.v1.endpoints.news import _normalize_category_id
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


class _FakeScalarResult:
    def __init__(self, items=None, scalar=None):
        self.items = items or []
        self.scalar = scalar

    def scalars(self):
        return self

    def all(self):
        return self.items

    def scalar_one(self):
        return self.scalar


class _FakeSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(str(statement))
        if "count(*)" in str(statement).lower():
            return _FakeScalarResult(scalar=11)
        return _FakeScalarResult(items=[_FakeNews()])


def test_get_news_list_filters_and_paginates():
    session = _FakeSession()

    async def fake_db():
        yield session

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/news/list?categoryId=1&page=2&pageSize=10")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["total"] == 11
    assert payload["data"]["hasMore"] is False
    assert payload["data"]["list"][0]["title"] == "测试新闻"
    assert "news.category_id = :category_id_1" in session.statements[0]


def test_get_news_list_requires_positive_category_id():
    response = TestClient(app).get("/api/news/list?categoryId=-1")

    assert response.status_code == 422


def test_empty_category_values_mean_all_categories():
    assert _normalize_category_id(None) is None
    assert _normalize_category_id("") is None
    assert _normalize_category_id("0") is None
    assert _normalize_category_id("none") is None
    assert _normalize_category_id("2") == 2
