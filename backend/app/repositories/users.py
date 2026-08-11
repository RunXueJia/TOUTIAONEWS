"""用户 API 模块的数据访问方法。"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


class DuplicateUsernameError(Exception):
    """数据库唯一约束表明用户名已被其他请求注册。"""


class UserRepository:
    """封装用户注册需要的查询与持久化操作。"""

    def __init__(self, db: AsyncSession) -> None:
        """使用请求级数据库会话初始化仓储。"""
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        """按用户名查询用户，不存在时返回空。"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, *, username: str, password: str) -> User:
        """保存新用户；并发导致用户名冲突时回滚并抛出业务异常。"""
        user = User(username=username, password=password)
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise DuplicateUsernameError from exc

        await self.db.refresh(user)
        return user
