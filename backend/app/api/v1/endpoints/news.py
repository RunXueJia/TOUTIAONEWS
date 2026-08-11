from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.news import NewsCategoryResponse, NewsDetailResponse, NewsListResponse
from app.services.news import NewsService, get_news_service


router = APIRouter(prefix="/news", tags=["news"])


def _normalize_category_id(category_id: str | None) -> int | None:
    """将缺失、空值、类空值和 0 统一视为不按分类筛选。"""
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
    summary="获取新闻列表",
    description="返回分页新闻列表。categoryId 省略、为空或为 0 时，返回全部分类的新闻。",
    response_description="分页新闻列表。",
    response_model=NewsListResponse,
    responses={422: {"description": "一个或多个查询参数不合法。"}},
)
async def get_news_list(
    category_id: str | None = Query(
        None,
        alias="categoryId",
        description="可选分类 ID。省略、留空、none、null 或 0 表示查询全部分类。",
    ),
    page: int = Query(1, ge=1, description="页码，从 1 开始，默认值为 1。"),
    page_size: int = Query(
        10,
        alias="pageSize",
        ge=1,
        le=100,
        description="每页记录数，默认 10，最大 100。",
    ),
    service: NewsService = Depends(get_news_service),
) -> dict[str, object]:
    """返回分页新闻列表，并按需按分类过滤。"""
    category_filter = _normalize_category_id(category_id)
    return await service.list_news(
        category_id=category_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/detail",
    summary="获取新闻详情",
    description="返回单篇新闻详情，自动增加浏览量，并附带相关文章。",
    response_description="目标新闻及其相关文章。",
    response_model=NewsDetailResponse,
    responses={
        404: {"description": "请求的新闻不存在。"},
        422: {"description": "新闻 ID 参数不合法。"},
    },
)
async def get_news_detail(
    news_id: int = Query(..., alias="id", ge=1, description="新闻文章 ID。"),
    service: NewsService = Depends(get_news_service),
) -> dict[str, object]:
    """根据新闻 ID 返回单条新闻详情。"""
    payload = await service.get_news_detail(news_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return payload


@router.get(
    "/categories",
    summary="获取新闻分类",
    description="按系统配置的展示顺序返回全部新闻分类。",
    response_description="按展示顺序排列的新闻分类列表。",
    response_model=list[NewsCategoryResponse],
)
async def get_news_categories(
    service: NewsService = Depends(get_news_service),
) -> list[dict[str, object]]:
    """返回按排序字段排列的新闻分类列表。"""
    return await service.list_categories()
