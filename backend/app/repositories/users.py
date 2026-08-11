"""用户 API 模块的数据访问方法。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User, UserToken


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

    async def get_token_by_user_id(self, user_id: int) -> UserToken | None:
        """按用户 ID 查询认证令牌，不存在时返回空。"""
        result = await self.db.execute(
            select(UserToken).where(UserToken.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_token(self, token: str) -> UserToken | None:
        """按令牌值查询认证令牌，不存在时返回空。"""
        result = await self.db.execute(select(UserToken).where(UserToken.token == token))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """按用户 ID 查询用户，不存在时返回空。"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_or_update_token(
        self,
        *,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> UserToken:
        """为用户创建令牌，已有令牌时更新令牌值和过期时间。"""
        user_token = await self.get_token_by_user_id(user_id)
        if user_token is None:
            user_token = UserToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
            )
            self.db.add(user_token)
        else:
            user_token.token = token
            user_token.expires_at = expires_at

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise

        await self.db.refresh(user_token)
        return user_token
