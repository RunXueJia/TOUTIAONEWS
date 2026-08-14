from datetime import datetime

from fastapi.testclient import TestClient

from app.db.database import get_db
from app.db.redis import get_redis
from main import app


class _FakeCategory:
    id = 1
    created_at = datetime(2023, 1, 1)
    updated_at = datetime(2023, 1, 2)
    name = "科技"
    sort_order = 0


class _FakeResult:
    """模拟 SQLAlchemy 分类查询结果。"""

    def scalars(self):
        """返回可继续调用 all 方法的标量结果。"""
        return self

    def all(self):
        """返回固定的模拟分类数据。"""
        return [_FakeCategory()]


class _FakeSession:
    def __init__(self) -> None:
        """记录分类查询次数，确保缓存命中时不再访问数据库。"""
        self.execute_calls = 0

    async def execute(self, statement):
        """模拟分类查询并累计数据库访问次数。"""
        assert "FROM news_category" in str(statement)
        self.execute_calls += 1
        return _FakeResult()


class _FakeRedis:
    """模拟分类接口所需的 Redis 读写行为。"""

    def __init__(self) -> None:
        """初始化内存缓存及写入记录。"""
        self.values: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def get(self, key: str) -> str | None:
        """返回指定键的缓存值。"""
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """保存缓存值并记录过期时间。"""
        self.values[key] = value
        self.set_calls.append((key, value, ex))


def test_get_news_categories_uses_redis_cache_for_7200_seconds():
    """分类接口首次查询后应缓存两小时，后续请求直接返回缓存。"""
    session = _FakeSession()
    redis_client = _FakeRedis()

    async def fake_db():
        """提供可统计查询次数的模拟数据库会话。"""
        yield session

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_redis] = lambda: redis_client
    try:
        client = TestClient(app)
        first_response = client.get("/api/news/categories")
        second_response = client.get("/api/news/categories")
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_redis, None)

    assert first_response.status_code == 200
    assert first_response.json()["code"] == 200
    assert first_response.json()["data"][0]["name"] == "科技"
    assert second_response.json()["data"] == first_response.json()["data"]
    assert session.execute_calls == 1
    assert redis_client.set_calls[0][0] == "news:categories"
    assert redis_client.set_calls[0][2] == 7200
