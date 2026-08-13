"""收藏模块路由与服务测试。"""

import asyncio
from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1.endpoints.favorite import router
from app.core.dependencies import get_current_user, get_optional_current_user
from app.db.database import get_db
from app.repositories.favorite import DuplicateFavoriteError
from app.services.favorite import FavoriteService, get_favorite_service
from main import app


class FakeFavoriteRepository:
    """为收藏状态测试提供内存仓储。"""

    def __init__(
        self,
        *,
        favorite_news_ids: set[int] | None = None,
        raise_duplicate_on_create: bool = False,
    ) -> None:
        """使用指定的已收藏新闻 ID 初始化仓储。"""
        self.favorite_news_ids = favorite_news_ids or set()
        self.received_user_id: int | None = None
        self.raise_duplicate_on_create = raise_duplicate_on_create
        self.deleted_news_id: int | None = None
        self.favorite_news = []

    async def create(self, *, user_id: int, news_id: int) -> SimpleNamespace:
        """记录新增收藏操作并返回用于响应序列化的收藏记录。"""
        self.received_user_id = user_id
        if self.raise_duplicate_on_create:
            raise DuplicateFavoriteError
        self.favorite_news_ids.add(news_id)
        return SimpleNamespace(
            id=1,
            user_id=user_id,
            news_id=news_id,
            created_at="2026-08-13T00:00:00",
        )

    async def exists(self, *, user_id: int, news_id: int) -> bool:
        """记录查询用户并返回预置的收藏状态。"""
        self.received_user_id = user_id
        return news_id in self.favorite_news_ids

    async def delete(self, *, user_id: int, news_id: int) -> bool:
        """记录删除收藏操作，并返回是否删除成功。"""
        self.received_user_id = user_id
        self.deleted_news_id = news_id
        if news_id not in self.favorite_news_ids:
            return False
        self.favorite_news_ids.remove(news_id)
        return True

    async def list_favorite_news(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[SimpleNamespace], int]:
        """返回预置的收藏新闻分页数据。"""
        self.received_user_id = user_id
        start = (page - 1) * page_size
        return self.favorite_news[start : start + page_size], len(self.favorite_news)


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


def test_add_news_favorite_requires_login_and_creates_record() -> None:
    """新增收藏应要求登录，并使用当前用户 ID 创建收藏记录。"""
    repository = FakeFavoriteRepository()

    async def fake_current_user() -> SimpleNamespace:
        """为路由测试注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为路由测试注入内存收藏服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        response = TestClient(app).post("/api/favorite/add", json={"newsId": 5})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["data"]["userId"] == 7
    assert response.json()["data"]["newsId"] == 5
    assert repository.received_user_id == 7


def test_favorite_add_response_serializes_orm_field_names() -> None:
    """新增收藏响应应能从 ORM 的下划线字段名读取别名字段。"""
    from datetime import datetime

    from app.schemas.favorite import FavoriteAddResponse

    favorite = SimpleNamespace(
        id=1,
        user_id=7,
        news_id=5,
        created_at=datetime(2026, 8, 13, 0, 0, 0),
    )

    assert FavoriteAddResponse.model_validate(favorite).model_dump(by_alias=True) == {
        "id": 1,
        "userId": 7,
        "newsId": 5,
        "created_at": datetime(2026, 8, 13, 0, 0, 0),
    }


def test_add_news_favorite_rejects_duplicate() -> None:
    """同一用户重复收藏同一新闻时应返回“已经收藏”业务错误。"""
    repository = FakeFavoriteRepository(favorite_news_ids={5})

    async def fake_current_user() -> SimpleNamespace:
        """为路由测试注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为路由测试注入预置收藏记录的服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        response = TestClient(app).post("/api/favorite/add", json={"newsId": 5})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert response.status_code == 200
    assert response.json() == {"code": 409, "message": "已经收藏", "data": None}


def test_add_news_favorite_handles_concurrent_duplicate() -> None:
    """数据库唯一约束捕获到并发重复写入时也应返回“已经收藏”。"""
    repository = FakeFavoriteRepository(raise_duplicate_on_create=True)

    async def fake_current_user() -> SimpleNamespace:
        """为路由测试注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为路由测试注入会模拟唯一约束冲突的服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        response = TestClient(app).post("/api/favorite/add", json={"newsId": 5})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert response.status_code == 200
    assert response.json() == {"code": 409, "message": "已经收藏", "data": None}


def test_remove_news_favorite_requires_login_and_deletes_record() -> None:
    """取消收藏应要求登录，先确认收藏存在后删除当前用户记录。"""
    repository = FakeFavoriteRepository(favorite_news_ids={5})

    async def fake_current_user() -> SimpleNamespace:
        """为路由测试注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为路由测试注入内存收藏服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        response = TestClient(app).delete("/api/favorite/remove?newsId=5")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert response.status_code == 200
    assert response.json() == {"code": 200, "message": "取消收藏成功", "data": None}
    assert repository.received_user_id == 7
    assert repository.deleted_news_id == 5
    assert 5 not in repository.favorite_news_ids


def test_remove_news_favorite_returns_not_found_when_not_collected() -> None:
    """当前用户未收藏目标新闻时不得执行删除，并返回业务 404。"""
    repository = FakeFavoriteRepository()

    async def fake_current_user() -> SimpleNamespace:
        """为路由测试注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为路由测试注入内存收藏服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        response = TestClient(app).delete("/api/favorite/remove?newsId=5")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert response.status_code == 200
    assert response.json() == {"code": 404, "message": "尚未收藏该新闻", "data": None}
    assert repository.deleted_news_id is None


def test_remove_news_favorite_validates_news_id() -> None:
    """取消收藏接口应拒绝非正整数新闻 ID。"""
    response = TestClient(app).delete("/api/favorite/remove?newsId=0")

    assert response.status_code == 200
    assert response.json()["code"] == 422


def test_get_favorite_news_list_requires_login_and_returns_pagination() -> None:
    """收藏列表应读取当前用户并返回新闻分页结构。"""
    repository = FakeFavoriteRepository()
    repository.favorite_news = [
        SimpleNamespace(
            id=1,
            publish_time=datetime(2026, 8, 13, 8, 0),
            created_at=datetime(2026, 8, 13, 8, 0),
            updated_at=datetime(2026, 8, 13, 8, 0),
            title="收藏新闻",
            description="简介",
            content="正文",
            image=None,
            author="作者",
            category_id=1,
            views=3,
        )
    ]

    async def fake_current_user() -> SimpleNamespace:
        """为收藏列表路由注入登录用户。"""
        return SimpleNamespace(id=7)

    async def fake_service() -> FavoriteService:
        """为收藏列表路由注入内存服务。"""
        return FavoriteService(repository)

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_favorite_service] = fake_service
    try:
        response = TestClient(app).get("/api/favorite/list?page=1&pageSize=1")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_favorite_service, None)

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "success",
        "data": {
            "list": [
                {
                    "id": 1,
                    "publish_time": "2026-08-13T08:00:00",
                    "created_at": "2026-08-13T08:00:00",
                    "updated_at": "2026-08-13T08:00:00",
                    "category": None,
                    "title": "收藏新闻",
                    "description": "简介",
                    "content": "正文",
                    "image": None,
                    "author": "作者",
                    "category_id": 1,
                    "views": 3,
                }
            ],
            "total": 1,
            "hasMore": False,
        },
    }
    assert repository.received_user_id == 7


def test_get_favorite_news_list_validates_pagination() -> None:
    """收藏列表应拒绝非正数页码和超出上限的每页数量。"""
    client = TestClient(app)

    assert client.get("/api/favorite/list?page=0").json()["code"] == 422
    assert client.get("/api/favorite/list?pageSize=101").json()["code"] == 422
