"""新闻 API 模块的业务服务。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.news import News, NewsCategory
from app.repositories.news import NewsRepository


class NewsService:
    """编排新闻业务流程，并避免在路由层暴露数据库查询细节。"""

    def __init__(self, repository: NewsRepository) -> None:
        """使用新闻仓储初始化服务对象。"""
        self.repository = repository

    async def list_news(
        self,
        *,
        category_id: int | None,
        page: int,
        page_size: int,
    ) -> dict[str, object]:
        """返回分页新闻列表，并支持按分类筛选。"""
        news_items, total = await self.repository.list_news(
            category_id=category_id,
            page=page,
            page_size=page_size,
        )
        return {
            "list": [self._serialize_news(item) for item in news_items],
            "total": total,
            "hasMore": page * page_size < total,
        }

    async def get_news_detail(self, news_id: int) -> dict[str, object] | None:
        """返回新闻详情并记录浏览量；新闻不存在时返回空。"""
        news_item = await self.repository.get_news_by_id(news_id)
        if news_item is None:
            return None

        await self.repository.increment_views(news_item)
        related_news = await self.repository.list_related_news(
            category_id=news_item.category_id,
            news_id=news_item.id,
        )
        payload = self._serialize_news(news_item)
        payload["relatedNews"] = [self._serialize_news(item) for item in related_news]
        return payload

    async def list_categories(self) -> list[dict[str, object]]:
        """按配置的展示顺序返回新闻分类列表。"""
        categories = await self.repository.list_categories()
        return [self._serialize_category(category) for category in categories]

    @staticmethod
    def _serialize_news(item: News) -> dict[str, object]:
        """将新闻 ORM 对象转换为对外接口字段。"""
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

    @staticmethod
    def _serialize_category(category: NewsCategory) -> dict[str, object]:
        """将新闻分类 ORM 对象转换为对外接口字段。"""
        return {
            "id": category.id,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "name": category.name,
            "sort_order": category.sort_order,
        }


def get_news_service(
    db: AsyncSession = Depends(get_db),
) -> NewsService:
    """提供一个基于请求级数据库会话的新闻服务实例。"""
    return NewsService(NewsRepository(db))
