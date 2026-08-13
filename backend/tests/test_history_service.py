"""浏览历史服务的行为测试。"""

import asyncio
from datetime import datetime
from types import SimpleNamespace

from app.services.history import HistoryService


class FakeHistoryRepository:
    """记录浏览历史服务调用参数的内存仓储。"""

    def __init__(self) -> None:
        """初始化空的调用记录。"""
        self.calls: list[tuple[int, int]] = []
        self.history_news: list[SimpleNamespace] = []
        self.clear_user_id: int | None = None

    async def create(self, *, user_id: int, news_id: int) -> SimpleNamespace:
        """模拟首次创建或重复浏览时刷新同一条记录。"""
        self.calls.append((user_id, news_id))
        return SimpleNamespace(
            id=1,
            user_id=user_id,
            news_id=news_id,
            view_time=datetime(2026, 8, 13, 12, 0, 0),
        )

    async def list_history_news(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[SimpleNamespace], int]:
        """模拟按浏览时间分页查询新闻，并记录当前用户。"""
        self.list_user_id = user_id
        start = (page - 1) * page_size
        return self.history_news[start : start + page_size], len(self.history_news)

    async def clear(self, *, user_id: int) -> int:
        """模拟按用户清空浏览记录并返回删除数量。"""
        self.clear_user_id = user_id
        return 2


def test_add_history_creates_or_refreshes_single_user_news_record() -> None:
    """首次和重复浏览均应委托仓储按用户与新闻唯一组合写入。"""

    async def verify() -> None:
        """执行两次相同浏览记录并断言写入目标不变。"""
        repository = FakeHistoryRepository()
        service = HistoryService(repository)

        first = await service.add_history(user_id=7, news_id=5)
        repeated = await service.add_history(user_id=7, news_id=5)

        assert first.id == repeated.id == 1
        assert repository.calls == [(7, 5), (7, 5)]

    asyncio.run(verify())


def test_list_history_news_returns_pagination_payload() -> None:
    """浏览历史列表应返回新闻字段、总数和下一页标记。"""

    async def verify() -> None:
        """执行浏览历史分页查询并校验用户范围和返回结构。"""
        repository = FakeHistoryRepository()
        repository.history_news = [
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
        service = HistoryService(repository)

        result = await service.list_history_news(user_id=7, page=1, page_size=1)

        assert result["total"] == 1
        assert result["hasMore"] is False
        assert result["list"][0]["id"] == 5
        assert repository.list_user_id == 7

    asyncio.run(verify())


def test_clear_history_deletes_only_current_user_records() -> None:
    """清空浏览历史应将当前用户 ID 传递给仓储并返回删除数量。"""

    async def verify() -> None:
        """执行清空操作并校验用户范围。"""
        repository = FakeHistoryRepository()
        service = HistoryService(repository)

        deleted = await service.clear_history(user_id=7)

        assert deleted == 2
        assert repository.clear_user_id == 7

    asyncio.run(verify())
