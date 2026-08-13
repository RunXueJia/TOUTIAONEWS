from datetime import datetime

from fastapi.testclient import TestClient

from app.db.database import get_db
from main import app


class _FakeNews:
    def __init__(self, news_id=1, title="测试新闻", views=10):
        self.id = news_id
        self.publish_time = datetime(2024, 1, 1, 8, 0)
        self.created_at = datetime(2026, 8, 10, 12, 0)
        self.updated_at = datetime(2026, 8, 10, 12, 0)
        self.title = title
        self.description = "简介"
        self.content = "正文"
        self.image = None
        self.author = "作者"
        self.category_id = 1
        self.views = views


class _FakeScalarResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


class _FakeSession:
    def __init__(self):
        self.executed_statements = []
        self.committed = False
        self.related_news = [
            _FakeNews(news_id=2, title="相关新闻一", views=80),
            _FakeNews(news_id=3, title="相关新闻二", views=50),
        ]

    async def get(self, model, news_id):
        return _FakeNews() if news_id == 1 else None

    async def execute(self, statement):
        self.executed_statements.append(str(statement))
        if str(statement).lstrip().startswith("SELECT"):
            return _FakeScalarResult(self.related_news)

    async def commit(self):
        self.committed = True

    async def refresh(self, instance, attribute_names):
        assert "views" in attribute_names
        assert "updated_at" in attribute_names
        if "views" in attribute_names:
            instance.views += 1


def test_get_news_detail_returns_article():
    session = _FakeSession()

    async def fake_db():
        yield session

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/news/detail?id=1")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["id"] == 1
    assert payload["data"]["content"] == "正文"
    assert payload["data"]["views"] == 11
    assert [item["id"] for item in payload["data"]["relatedNews"]] == [2, 3]
    assert [item["views"] for item in payload["data"]["relatedNews"]] == [80, 50]
    assert session.committed is True
    assert "news.views + :views_1" in session.executed_statements[0]
    assert "news.category_id = :category_id_1" in session.executed_statements[1]
    assert "news.id != :id_1" in session.executed_statements[1]
    assert "LIMIT :param_1" in session.executed_statements[1]
    assert "ORDER BY news.views DESC" in session.executed_statements[1]


def test_get_news_detail_returns_not_found():
    session = _FakeSession()

    async def fake_db():
        yield session

    app.dependency_overrides[get_db] = fake_db
    try:
        response = TestClient(app).get("/api/news/detail?id=999")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == {
        "code": 404,
        "message": "News article not found",
        "data": None,
    }


def test_get_news_detail_requires_positive_id():
    response = TestClient(app).get("/api/news/detail?id=0")
    assert response.status_code == 200
    assert response.json()["code"] == 422
