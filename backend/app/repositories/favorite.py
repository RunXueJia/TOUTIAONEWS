"""收藏模块的数据访问方法。"""

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import Favorite, News


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

    async def delete(self, *, user_id: int, news_id: int) -> bool:
        """删除指定用户对指定新闻的收藏记录，并返回是否实际删除。"""
        result = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.news_id == news_id,
            ).limit(1)
        )
        favorite = result.scalar_one_or_none()
        if favorite is None:
            return False

        await self.db.delete(favorite)
        await self.db.commit()
        return True

    async def clear(self, *, user_id: int) -> int:
        """删除指定用户的全部收藏记录，并返回实际删除的记录数。"""
        result = await self.db.execute(delete(Favorite).where(Favorite.user_id == user_id))
        await self.db.commit()
        return int(result.rowcount or 0)

    async def list_favorite_news(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[News], int]:
        """联表查询用户收藏的新闻，并返回当前页记录及总数。"""
        favorite_filter = Favorite.user_id == user_id
        total_result = await self.db.execute(
            select(func.count())
            .select_from(Favorite)
            .join(News, News.id == Favorite.news_id)
            .where(favorite_filter)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(News)
            .join(Favorite, Favorite.news_id == News.id)
            .where(favorite_filter)
            .order_by(Favorite.created_at.desc(), Favorite.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
