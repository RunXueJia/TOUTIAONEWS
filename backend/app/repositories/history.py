"""浏览历史模块的数据访问方法。"""

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import History, News


class HistoryRepository:
    """封装浏览历史记录的持久化操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """使用请求级数据库会话初始化浏览历史仓储。"""
        self.db = db

    async def get_news_by_id(self, news_id: int) -> News | None:
        """按主键查询新闻，用于删除浏览记录前确认新闻存在。"""
        return await self.db.get(News, news_id)

    async def exists(self, *, user_id: int, news_id: int) -> bool:
        """判断指定用户是否存在目标新闻的浏览记录。"""
        result = await self.db.execute(
            select(History.id)
            .where(History.user_id == user_id, History.news_id == news_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, *, user_id: int, news_id: int) -> bool:
        """删除指定用户的目标新闻浏览记录，并返回是否实际删除。"""
        result = await self.db.execute(
            select(History)
            .where(History.user_id == user_id, History.news_id == news_id)
            .limit(1)
        )
        history = result.scalar_one_or_none()
        if history is None:
            return False

        await self.db.delete(history)
        await self.db.commit()
        return True

    async def clear(self, *, user_id: int) -> int:
        """删除指定用户的全部浏览记录，并返回实际删除的记录数。"""
        result = await self.db.execute(delete(History).where(History.user_id == user_id))
        await self.db.commit()
        return int(result.rowcount or 0)

    async def create(self, *, user_id: int, news_id: int) -> History:
        """新增或刷新浏览记录，并清理历史重复数据以保持用户新闻组合唯一。"""
        records = list(
            (
                await self.db.execute(
                    select(History)
                    .where(
                        History.user_id == user_id,
                        History.news_id == news_id,
                    )
                    .order_by(History.view_time.desc(), History.id.desc())
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        if records:
            history = records[0]
            history.view_time = func.now()
            for duplicate in records[1:]:
                await self.db.delete(duplicate)
            await self.db.commit()
            await self.db.refresh(history)
            return history

        history = History(user_id=user_id, news_id=news_id)
        self.db.add(history)
        try:
            await self.db.commit()
        except IntegrityError:
            # 并发首次写入被联合唯一约束拦截后，改为刷新已创建的那条记录。
            await self.db.rollback()
            return await self.create(user_id=user_id, news_id=news_id)

        await self.db.refresh(history)
        return history

    async def create_or_update(self, *, user_id: int, news_id: int) -> History:
        """兼容旧调用方，委托新增或刷新浏览记录的统一实现。"""
        return await self.create(user_id=user_id, news_id=news_id)

    async def list_history_news(
        self,
        *,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[News], int]:
        """联表查询当前用户浏览过的新闻，并返回当前页记录及总数。"""
        history_filter = History.user_id == user_id
        total_result = await self.db.execute(
            select(func.count())
            .select_from(History)
            .join(News, News.id == History.news_id)
            .where(history_filter)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(News)
            .join(History, History.news_id == News.id)
            .where(history_filter)
            .order_by(History.view_time.desc(), History.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
