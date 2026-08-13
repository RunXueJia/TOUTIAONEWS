"""收藏模块的数据访问方法。"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import Favorite


class DuplicateFavoriteError(Exception):
    """数据库唯一约束表明同一用户已收藏指定新闻。"""


class FavoriteRepository:
    """封装收藏记录的查询与持久化操作。"""

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

    async def create(self, *, user_id: int, news_id: int) -> Favorite:
        """创建收藏记录；重复写入时回滚并抛出明确的业务数据访问异常。"""
        favorite = Favorite(user_id=user_id, news_id=news_id)
        self.db.add(favorite)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateFavoriteError from exc

        await self.db.refresh(favorite)
        return favorite
