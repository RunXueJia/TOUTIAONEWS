"""Data access methods for the news API module."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News, NewsCategory


class NewsRepository:
    """Encapsulate ORM queries and CRUD operations for news resources."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_news(
        self,
        *,
        category_id: int | None,
        page: int,
        page_size: int,
    ) -> tuple[list[News], int]:
        """Return one page of news for a category and the matching total."""
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
        """Return one news article by primary key, if it exists."""
        return await self.db.get(News, news_id)

    async def increment_views(self, news: News) -> News:
        """Atomically increase a news article's view count and refresh it."""
        await self.db.execute(
            update(News)
            .where(News.id == news.id)
            .values(views=News.views + 1)
        )
        await self.db.commit()
        await self.db.refresh(news, attribute_names=["views"])
        return news

    async def list_related_news(
        self,
        *,
        category_id: int,
        news_id: int,
    ) -> list[News]:
        """Return the five newest same-category articles, ranked by views."""
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
        """Return all news categories in display order."""
        result = await self.db.execute(
            select(NewsCategory).order_by(
                NewsCategory.sort_order.asc(),
                NewsCategory.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: int) -> NewsCategory | None:
        """Return one news category by primary key, if it exists."""
        return await self.db.get(NewsCategory, category_id)

    async def create_category(self, name: str, sort_order: int = 0) -> NewsCategory:
        """Create and persist a news category."""
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
        """Update supplied fields on a news category."""
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
        """Delete a category and return whether a row was removed."""
        category = await self.get_category_by_id(category_id)
        if category is None:
            return False

        await self.db.delete(category)
        await self.db.commit()
        return True
