"""Data access methods for the news API module."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news_category import NewsCategory


class NewsRepository:
    """Encapsulate ORM queries and CRUD operations for news resources."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
