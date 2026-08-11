"""用户 API 模块的业务服务。"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.users import User
from app.repositories.users import DuplicateUsernameError, UserRepository
from app.utils.password import hash_password


class UsernameAlreadyExistsError(Exception):
    """注册用户名已存在时抛出的业务异常。"""


class UserService:
    """编排用户注册规则并隔离密码加密细节。"""

    def __init__(self, repository: UserRepository) -> None:
        """使用用户仓储初始化服务对象。"""
        self.repository = repository

    async def register(self, *, username: str, password: str) -> dict[str, object]:
        """校验用户名唯一性、加密密码并创建用户。"""
        if await self.repository.get_by_username(username) is not None:
            raise UsernameAlreadyExistsError

        try:
            user = await self.repository.create_user(
                username=username,
                password=hash_password(password),
            )
        except DuplicateUsernameError as exc:
            raise UsernameAlreadyExistsError from exc

        return {"userInfo": self._serialize_user(user)}

    @staticmethod
    def _serialize_user(user: User) -> dict[str, object]:
        """转换用户公开字段，避免将密码哈希暴露给调用方。"""
        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }


def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    """提供一个使用请求级数据库会话的用户服务实例。"""
    return UserService(UserRepository(db))
