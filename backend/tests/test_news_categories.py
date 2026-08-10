from datetime import datetime

from fastapi.testclient import TestClient

from app.db.database import get_db
from main import app


class _FakeCategory:
    id = 1
    created_at = datetime(2023, 1, 1)
    updated_at = datetime(2023, 1, 2)
    name = "科技"
    sort_order = 0


class _FakeResult:
    def scalars(self):
        return self

    def all(self):
        return [_FakeCategory()]


class _FakeSession:
    async def execute(self, statement):
        assert "FROM news_category" in str(statement)
        return _FakeResult()


async def _fake_db():
    yield _FakeSession()


def test_get_news_categories():
    app.dependency_overrides[get_db] = _fake_db
    try:
        response = TestClient(app).get("/api/news/categories")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["data"][0]["name"] == "科技"
