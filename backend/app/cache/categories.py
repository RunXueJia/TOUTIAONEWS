"""新闻分类 Redis 缓存操作。"""

from typing import Any

from redis.asyncio import Redis

from app.db.redis import get_cache, set_cache


CATEGORIES_CACHE_KEY = "news:categories"
CATEGORIES_CACHE_EXPIRE_SECONDS = 7200


async def get_categories_cache(redis_client: Redis) -> Any | None:
    """读取全部新闻分类缓存。"""
    return await get_cache(redis_client, CATEGORIES_CACHE_KEY)


async def set_categories_cache(
    redis_client: Redis,
    value: Any,
    *,
    expire_seconds: int = CATEGORIES_CACHE_EXPIRE_SECONDS,
) -> None:
    """写入全部新闻分类缓存。"""
    await set_cache(
        redis_client,
        CATEGORIES_CACHE_KEY,
        value,
        expire_seconds=expire_seconds,
    )
