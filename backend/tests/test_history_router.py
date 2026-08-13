"""浏览历史列表路由测试。"""

from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.services.history import HistoryService, get_history_service
from main import app


class FakeHistoryListRepository:
    """为浏览历史列表路由提供内存新闻数据。"""

    def __init__(self) -> None:
        """初始化一条浏览历史新闻。"""
        self.user_id: int | None = None
        self.items = [
            SimpleNamespace(
                id=5,
                publish_time=datetime(2026, 8, 13, 8, 0),
                created_at=datetime(2026, 8, 13, 8, 0),
                updated_at=datetime(2026, 8, 13, 8, 0),
                title="历史新闻",
                description="简介",
                content="正文",
                image=None,
                author="作者",
                category_id=1,
                views=3,
            )
        ]

    async def list_history_news(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[SimpleNamespace], int]:
        """记录用户 ID 并返回分页新闻。"""
        self.user_id = user_id
        start = (page - 1) * page_size
        return self.items[start : start + page_size], len(self.items)


def test_get_history_list_uses_current_user_and_returns_pagination() -> None:
    """浏览历史列表应使用认证用户并返回统一分页结构。"""
    repository = FakeHistoryListRepository()

    async def fake_current_user() -> SimpleNamespace:
        """注入已登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> HistoryService:
        """注入内存浏览历史服务。"""
        return HistoryService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_history_service] = fake_service
    try:
        response = TestClient(app).get("/api/history/list?page=1&pageSize=1")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_history_service, None)

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1
    assert response.json()["data"]["hasMore"] is False
    assert response.json()["data"]["list"][0]["id"] == 5
    assert repository.user_id == 7


def test_get_history_list_validates_pagination() -> None:
    """浏览历史列表应拒绝非法分页参数。"""
    client = TestClient(app)

    assert client.get("/api/history/list?page=0").json()["code"] == 422
    assert client.get("/api/history/list?pageSize=101").json()["code"] == 422
