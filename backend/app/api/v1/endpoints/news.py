from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.news import NewsRepository


router = APIRouter(prefix="/news", tags=["news"])

@router.get("/categories")
async def get_news_categories(db: AsyncSession = Depends(get_db)) -> list[dict[str, object]]:
    """Return news categories ordered by their configured sort order."""
    categories = await NewsRepository(db).list_categories()
    return [
        {
            "id": category.id,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "name": category.name,
            "sort_order": category.sort_order,
        }
        for category in categories
    ]
