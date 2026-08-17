"""新闻领域 Redis 缓存操作。"""

from app.cache.categories import get_categories_cache, set_categories_cache
from app.cache.news import get_news_list_cache, set_news_list_cache

__all__ = [
    "get_categories_cache",
    "get_news_list_cache",
    "set_categories_cache",
    "set_news_list_cache",
]
