"""收藏模块路由与服务测试。"""

import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.endpoints.favorite import router
from app.core.dependencies import get_optional_current_user
from app.db.database import get_db
from app.services.favorite import FavoriteService, get_favorite_service
from main import app


class FakeFavoriteRepository:
    """为收藏状态测试提供内存仓储。"""

    def __init__(self, *, favorite_news_ids: set[int] | None = None) -> None:
        """使用指定的已收藏新闻 ID 初始化仓储。"""
        self.favorite_news_ids = favorite_news_ids or set()
        self.received_user_id: int | None = None

    async def exists(self, *, user_id: int, news_id: int) -> bool:
        """记录查询用户并返回预置的收藏状态。"""
        self.received_user_id = user_id
        return news_id in self.favorite_news_ids


def test_favorite_router_allows_anonymous_check() -> None:
    """收藏状态查询路由不应在模块级强制登录。"""
    assert router.dependencies == []

    check_route = next(route for route in router.routes if route.path == "/favorite/check")
    dependency_calls = [dependency.dependency for dependency in check_route.dependant.dependencies]

    assert get_optional_current_user in dependency_calls


def test_favorite_service_returns_false_for_anonymous_user() -> None:
    """匿名用户查询收藏状态时不访问数据库并返回未收藏。"""
    async def verify() -> None:
        repository = FakeFavoriteRepository(favorite_news_ids={1})
        result = await FavoriteService(repository).is_news_favorited(user_id=None, news_id=1)

        assert result == {"isFavorite": False}
        assert repository.received_user_id is None

    asyncio.run(verify())


def test_check_news_favorite_returns_status_for_authenticated_user() -> None:
    """已登录用户应按用户 ID 和新闻 ID 返回收藏状态。"""
    repository = FakeFavoriteRepository(favorite_news_ids={5})

    async def fake_current_user() -> SimpleNamespace:
        """为路由测试注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为路由测试注入收藏服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_optional_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        client = TestClient(app)
        favorited_response = client.get("/api/favorite/check?newsId=5")
        not_favorited_response = client.get("/api/favorite/check?newsId=6")
    finally:
        app.dependency_overrides.pop(get_optional_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert favorited_response.status_code == 200
    assert favorited_response.json() == {
        "code": 200,
        "message": "success",
        "data": {"isFavorite": True},
    }
    assert not_favorited_response.status_code == 200
    assert not_favorited_response.json()["data"] == {"isFavorite": False}
    assert repository.received_user_id == 7


def test_check_news_favorite_allows_missing_login_and_validates_news_id() -> None:
    """未登录不得报认证错误，newsId 仍必须是正整数。"""
    async def fake_current_user() -> None:
        """为路由测试模拟未登录状态。"""
        return None

    async def fake_db():
        """未登录路径不应使用数据库，但仍提供可注入的空会话。"""
        yield object()

    app.dependency_overrides[get_optional_current_user] = fake_current_user
    app.dependency_overrides[get_db] = fake_db
    try:
        client = TestClient(app)
        anonymous_response = client.get("/api/favorite/check?newsId=1")
        invalid_response = client.get("/api/favorite/check?newsId=0")
    finally:
        app.dependency_overrides.pop(get_optional_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    assert anonymous_response.status_code == 200
    assert anonymous_response.json()["data"] == {"isFavorite": False}
    assert invalid_response.status_code == 200
    assert invalid_response.json()["code"] == 422
