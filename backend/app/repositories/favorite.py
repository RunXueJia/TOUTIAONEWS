"""收藏模块的数据访问方法。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import Favorite


class FavoriteRepository:
    """封装收藏记录的查询操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """使用请求级数据库会话初始化收藏仓储。"""
        self.db = db

    async def exists(self, *, user_id: int, news_id: int) -> bool:
        """判断指定用户是否已收藏指定新闻。"""
        result = await self.db.execute(
            select(Favorite.id).where(
                Favorite.user_id == user_id,
                Favorite.news_id == news_id,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None
