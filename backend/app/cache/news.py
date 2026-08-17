"""新闻列表 Redis 缓存操作。"""

from typing import Any

from redis.asyncio import Redis

from app.db.redis import get_cache, set_cache


NEWS_LIST_CACHE_EXPIRE_SECONDS = 300


def build_news_list_cache_key(
    *,
    category_id: int | None,
    page: int,
    page_size: int,
) -> str:
    """按分类、页码和分页大小生成新闻列表缓存键。

    分类为空表示全部分类，使用约定的分类 ID ``0`` 保持键结构稳定。
    """
    normalized_category_id = 0 if category_id is None else category_id
    return f"news:list:{normalized_category_id}:{page}:{page_size}"


async def get_news_list_cache(
    redis_client: Redis,
    *,
    category_id: int | None,
    page: int,
    page_size: int,
) -> Any | None:
    """读取指定分页条件下的新闻列表缓存。"""
    return await get_cache(
        redis_client,
        build_news_list_cache_key(
            category_id=category_id,
            page=page,
            page_size=page_size,
        ),
    )


async def set_news_list_cache(
    redis_client: Redis,
    value: Any,
    *,
    category_id: int | None,
    page: int,
    page_size: int,
    expire_seconds: int = NEWS_LIST_CACHE_EXPIRE_SECONDS,
) -> None:
    """写入指定分页条件下的新闻列表缓存。"""
    await set_cache(
        redis_client,
        build_news_list_cache_key(
            category_id=category_id,
            page=page,
            page_size=page_size,
        ),
        value,
        expire_seconds=expire_seconds,
    )
