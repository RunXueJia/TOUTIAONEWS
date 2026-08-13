"""新闻 API 模块的数据访问方法。"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News, NewsCategory


class NewsRepository:
    """封装新闻相关的 ORM 查询与增删改查操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """使用请求级数据库会话初始化仓储对象。"""
        self.db = db

    async def list_news(
        self,
        *,
        category_id: int | None,
        page: int,
        page_size: int,
    ) -> tuple[list[News], int]:
        """返回指定分类下的一页新闻数据及总条数。"""
        base_query = select(News)
        if category_id not in (None, 0):
            base_query = base_query.where(News.category_id == category_id)

        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            base_query.order_by(News.publish_time.desc(), News.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_news_by_id(self, news_id: int) -> News | None:
        """按主键查询单条新闻，不存在时返回空。"""
        return await self.db.get(News, news_id)

    async def increment_views(self, news: News) -> News:
        """原子性增加新闻浏览量，并刷新最新值。"""
        await self.db.execute(
            update(News)
            .where(News.id == news.id)
            .values(views=News.views + 1)
        )
        await self.db.commit()
        # 提交会使带有 server/onupdate 的 updated_at 属性过期；异步会话中
        # 后续序列化不能依赖隐式懒加载，必须在这里显式刷新该字段。
        await self.db.refresh(news, attribute_names=["views", "updated_at"])
        return news

    async def list_related_news(
        self,
        *,
        category_id: int,
        news_id: int,
    ) -> list[News]:
        """返回同分类下最新五条新闻，并按浏览量重新排序。"""
        recent_news = (
            select(News.id)
            .where(
                News.category_id == category_id,
                News.id != news_id,
            )
            .order_by(News.publish_time.desc(), News.id.desc())
            .limit(5)
            .subquery()
        )
        result = await self.db.execute(
            select(News)
            .join(recent_news, News.id == recent_news.c.id)
            .order_by(
                News.views.desc(),
                News.publish_time.desc(),
                News.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_categories(self) -> list[NewsCategory]:
        """按展示顺序返回全部新闻分类。"""
        result = await self.db.execute(
            select(NewsCategory).order_by(
                NewsCategory.sort_order.asc(),
                NewsCategory.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: int) -> NewsCategory | None:
        """按主键查询单个新闻分类，不存在时返回空。"""
        return await self.db.get(NewsCategory, category_id)

    async def create_category(self, name: str, sort_order: int = 0) -> NewsCategory:
        """创建并持久化一个新闻分类。"""
        category = NewsCategory(name=name, sort_order=sort_order)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update_category(
        self,
        category_id: int,
        *,
        name: str | None = None,
        sort_order: int | None = None,
    ) -> NewsCategory | None:
        """更新新闻分类中传入的字段。"""
        category = await self.get_category_by_id(category_id)
        if category is None:
            return None

        if name is not None:
            category.name = name
        if sort_order is not None:
            category.sort_order = sort_order

        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete_category(self, category_id: int) -> bool:
        """删除新闻分类，并返回是否实际删除了记录。"""
        category = await self.get_category_by_id(category_id)
        if category is None:
            return False

        await self.db.delete(category)
        await self.db.commit()
        return True
