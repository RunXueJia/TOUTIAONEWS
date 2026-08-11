from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.news import News
from app.repositories.news import NewsRepository


router = APIRouter(prefix="/news", tags=["news"])


def _serialize_news(item: News) -> dict[str, object]:
    """Convert a news ORM object into the public API representation."""
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


def _normalize_category_id(category_id: str | None) -> int | None:
    """Treat missing, empty, null-like and zero category values as no filter."""
    normalized = (category_id or "").strip()
    if not normalized or normalized.lower() in {"none", "null", "0"}:
        return None

    try:
        parsed = int(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="categoryId must be a positive integer") from exc

    if parsed == 0:
        return None
    if parsed < 0:
        raise HTTPException(status_code=422, detail="categoryId must be a positive integer")
    return parsed


@router.get(
    "/list",
    summary="Get news list",
    description="Return paginated news. An omitted or empty categoryId returns news from all categories.",
)
async def get_news_list(
    category_id: str | None = Query(
        None,
        alias="categoryId",
        description="Optional category ID. Omit, empty, none, null, or 0 to query all categories.",
    ),
    page: int = Query(1, ge=1, description="Page number starting at 1 (default: 1)."),
    page_size: int = Query(
        10,
        alias="pageSize",
        ge=1,
        le=100,
        description="Records per page (default: 10, maximum: 100).",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Return a paginated news list, optionally filtered by category."""
    category_filter = _normalize_category_id(category_id)
    news_items, total = await NewsRepository(db).list_news(
        category_id=category_filter,
        page=page,
        page_size=page_size,
    )
    return {
        "list": [_serialize_news(item) for item in news_items],
        "total": total,
        "hasMore": page * page_size < total,
    }


@router.get("/detail", summary="Get news detail")
async def get_news_detail(
    news_id: int = Query(..., alias="id", ge=1, description="News article ID."),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Return a single news article by its ID."""
    repository = NewsRepository(db)
    news_item = await repository.get_news_by_id(news_id)
    if news_item is None:
        raise HTTPException(status_code=404, detail="News article not found")
    await repository.increment_views(news_item)
    related_news = await repository.list_related_news(
        category_id=news_item.category_id,
        news_id=news_item.id,
    )
    payload = _serialize_news(news_item)
    payload["relatedNews"] = [_serialize_news(item) for item in related_news]
    return payload


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
