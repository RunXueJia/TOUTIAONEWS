"""新闻列表 Redis 缓存行为测试。"""

import asyncio
from datetime import datetime
from types import SimpleNamespace

from app.cache.news import build_news_list_cache_key
from app.services.news import NewsService


class _FakeRedis:
    """模拟新闻列表缓存所需的 Redis get/set 行为。"""

    def __init__(self) -> None:
        """初始化内存缓存和写入记录。"""
        self.values: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def get(self, key: str) -> str | None:
        """读取内存中的缓存值。"""
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """保存缓存值并记录有效期。"""
        self.values[key] = value
        self.set_calls.append((key, value, ex))


class _FakeRepository:
    """记录新闻列表数据库查询次数的仓储替身。"""

    def __init__(self) -> None:
        """初始化一条可序列化的新闻记录。"""
        self.calls = 0
        self.article = SimpleNamespace(
            id=1,
            publish_time=datetime(2026, 1, 1),
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
            title="缓存新闻",
            description=None,
            content="正文",
            image=None,
            author="作者",
            category_id=2,
            views=3,
        )

    async def list_news(self, **_kwargs: object) -> tuple[list[SimpleNamespace], int]:
        """模拟一次分页数据库查询。"""
        self.calls += 1
        return [self.article], 1


def test_news_list_cache_key_uses_zero_for_all_categories() -> None:
    """全部分类和指定分类应生成稳定且可区分的分页键。"""
    assert build_news_list_cache_key(category_id=None, page=2, page_size=20) == "news:list:0:2:20"
    assert build_news_list_cache_key(category_id=3, page=2, page_size=20) == "news:list:3:2:20"


def test_news_service_reads_and_writes_paginated_cache() -> None:
    """首次查询写入缓存，后续相同分页请求不再访问仓储。"""
    async def verify() -> None:
        repository = _FakeRepository()
        redis_client = _FakeRedis()
        service = NewsService(repository, redis_client)

        first = await service.list_news(category_id=2, page=1, page_size=10)
        second = await service.list_news(category_id=2, page=1, page_size=10)

        assert first["list"][0]["id"] == second["list"][0]["id"]
        assert first["total"] == second["total"]
        assert first["hasMore"] == second["hasMore"]
        assert repository.calls == 1
        assert redis_client.set_calls[0][0] == "news:list:2:1:10"
        assert redis_client.set_calls[0][2] == 300

    asyncio.run(verify())
