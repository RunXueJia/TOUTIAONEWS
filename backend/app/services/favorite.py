"""收藏模块的业务服务。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.news import Favorite
from app.repositories.favorite import DuplicateFavoriteError, FavoriteRepository


class FavoriteAlreadyExistsError(Exception):
    """用户重复收藏同一新闻时抛出的业务异常。"""


class FavoriteService:
    """编排用户收藏状态的查询业务。"""

    def __init__(self, repository: FavoriteRepository) -> None:
        """使用收藏仓储初始化服务对象。"""
        self.repository = repository

    async def is_news_favorited(self, *, user_id: int | None, news_id: int) -> dict[str, bool]:
        """返回新闻收藏状态；匿名用户始终返回未收藏。"""
        if user_id is None:
            return {"isFavorite": False}

        return {
            "isFavorite": await self.repository.exists(
                user_id=user_id,
                news_id=news_id,
            )
        }

    async def add_news_favorite(self, *, user_id: int, news_id: int) -> Favorite:
        """校验未重复收藏后创建记录，并将并发冲突转换为重复收藏业务异常。"""
        if await self.repository.exists(user_id=user_id, news_id=news_id):
            raise FavoriteAlreadyExistsError

        try:
            return await self.repository.create(user_id=user_id, news_id=news_id)
        except DuplicateFavoriteError as exc:
            raise FavoriteAlreadyExistsError from exc


def get_favorite_service(
    db: AsyncSession = Depends(get_db),
) -> FavoriteService:
    """提供一个使用请求级数据库会话的收藏服务实例。"""
    return FavoriteService(FavoriteRepository(db))
