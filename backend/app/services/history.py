"""浏览历史模块的业务服务。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.news import History, News
from app.repositories.history import HistoryRepository


class HistoryNewsNotFoundError(Exception):
    """删除浏览记录时目标新闻不存在。"""


class HistoryNotFoundError(Exception):
    """当前用户尚未产生目标新闻的浏览记录。"""


class HistoryService:
    """编排用户浏览历史的查询与新增业务。"""

    def __init__(self, repository: HistoryRepository) -> None:
        """使用浏览历史仓储初始化服务对象。"""
        self.repository = repository

    async def add_history(self, *, user_id: int, news_id: int) -> History:
        """记录当前用户的新闻浏览行为；重复浏览仅刷新最近浏览时间。"""
        return await self.repository.create(user_id=user_id, news_id=news_id)

    async def delete_history(self, *, user_id: int, news_id: int) -> None:
        """按新闻 ID 删除当前用户的浏览记录，并校验新闻及记录均存在。"""
        if await self.repository.get_news_by_id(news_id) is None:
            raise HistoryNewsNotFoundError
        if not await self.repository.exists(user_id=user_id, news_id=news_id):
            raise HistoryNotFoundError
        await self.repository.delete(user_id=user_id, news_id=news_id)

    async def clear_history(self, *, user_id: int) -> int:
        """清空当前用户的全部浏览记录，并返回删除的记录数。"""
        return await self.repository.clear(user_id=user_id)

    async def list_history_news(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> dict[str, object]:
        """返回当前用户浏览历史的分页新闻列表及下一页标记。"""
        news_items, total = await self.repository.list_history_news(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        return {
            "list": [self._serialize_news(item) for item in news_items],
            "total": total,
            "hasMore": page * page_size < total,
        }

    @staticmethod
    def _serialize_news(item: News) -> dict[str, object]:
        """将新闻 ORM 对象转换为浏览历史列表对外返回的字段。"""
        return {
            "id": item.id,
            "publish_time": item.publish_time,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "category": None,
            "title": item.title,
            "description": item.description,
            "content": item.content,
            "image": item.image,
            "author": item.author,
            "category_id": item.category_id,
            "views": item.views,
        }


def get_history_service(
    db: AsyncSession = Depends(get_db),
) -> HistoryService:
    """提供一个使用请求级数据库会话的浏览历史服务实例。"""
    return HistoryService(HistoryRepository(db))
