"""用户 API 模块的业务服务。"""

import secrets
from datetime import datetime, timedelta

from fastapi import Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.users import User
from app.repositories.users import DuplicateUsernameError, UserRepository
from app.utils.password import hash_password, verify_password


class UsernameAlreadyExistsError(Exception):
    """注册用户名已存在时抛出的业务异常。"""


class InvalidCredentialsError(Exception):
    """登录用户名不存在或密码校验失败时抛出的业务异常。"""


class TokenNotFoundError(Exception):
    """请求令牌不存在或无法关联用户时抛出的业务异常。"""


class TokenExpiredError(Exception):
    """请求令牌已超过有效期时抛出的业务异常。"""


class OldPasswordIncorrectError(Exception):
    """提交的旧密码与当前用户密码不一致时抛出的业务异常。"""


class PasswordUnchangedError(Exception):
    """新密码与旧密码一致时抛出的业务异常。"""


class UserService:
    """编排用户注册和登录规则并隔离密码与令牌细节。"""

    def __init__(self, repository: UserRepository) -> None:
        """使用用户仓储初始化服务对象。"""
        self.repository = repository

    async def register(
        self,
        *,
        username: str,
        password: str,
        response: Response | None = None,
    ) -> dict[str, object]:
        """校验用户名唯一性、加密密码、创建用户并生成认证令牌。"""
        if await self.repository.get_by_username(username) is not None:
            raise UsernameAlreadyExistsError

        try:
            user = await self.repository.create_user(
                username=username,
                password=hash_password(password),
            )
        except DuplicateUsernameError as exc:
            raise UsernameAlreadyExistsError from exc

        token = await self.generate_token(user.id, response=response)
        return {"token": token, "userInfo": self._serialize_user(user)}

    async def generate_token(
        self,
        user_id: int,
        *,
        response: Response | None = None,
    ) -> str:
        """为用户生成认证令牌并写入 Cookie；已有令牌会被刷新。"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        user_token = await self.repository.create_or_update_token(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self._set_token_cookie(response, user_token.token, user_token.expires_at)
        return user_token.token

    async def login(
        self,
        *,
        username: str,
        password: str,
        response: Response | None = None,
    ) -> dict[str, object]:
        """查询并校验用户凭据，复用有效令牌或创建新的七日令牌。"""
        user = await self.repository.get_by_username(username)
        if user is None or not verify_password(password, user.password):
            raise InvalidCredentialsError

        user_token = await self.repository.get_token_by_user_id(user.id)
        now = datetime.now()
        if user_token is None or user_token.expires_at <= now:
            token = await self.generate_token(user.id, response=response)
        else:
            token = user_token.token
            self._set_token_cookie(response, token, user_token.expires_at)

        return {"token": token, "userInfo": self._serialize_user(user)}

    async def validate_token(self, authorization: str | None) -> User:
        """校验 Authorization 令牌，并返回已认证用户供受保护接口复用。"""
        token = self._normalize_authorization(authorization)
        if not token:
            raise TokenNotFoundError

        user_token = await self.repository.get_token(token)
        if user_token is None:
            raise TokenNotFoundError
        if user_token.expires_at <= datetime.now():
            raise TokenExpiredError

        user = await self.repository.get_by_id(user_token.user_id)
        if user is None:
            raise TokenNotFoundError
        return user

    async def get_user_info(self, authorization: str | None) -> dict[str, object]:
        """校验令牌后返回当前用户公开信息，兼容已有用户信息调用。"""
        user = await self.validate_token(authorization)
        return self._serialize_user(user)

    async def update_user(self, user: User, update_data: dict[str, object]) -> User:
        """仅保存当前用户明确提交的非账号资料字段。"""
        allowed_fields = {"nickname", "avatar", "gender", "bio"}
        profile_data = {
            field: value for field, value in update_data.items() if field in allowed_fields
        }
        if not profile_data:
            return user
        return await self.repository.update_user(user, profile_data)

    async def update_password(
        self,
        user: User,
        *,
        old_password: str,
        new_password: str,
    ) -> User:
        """校验旧密码和新旧差异后，保存当前用户的新密码哈希。"""
        if not verify_password(old_password, user.password):
            raise OldPasswordIncorrectError
        if new_password == old_password:
            raise PasswordUnchangedError
        return await self.repository.update_password(user, hash_password(new_password))

    @staticmethod
    def _normalize_authorization(authorization: str | None) -> str:
        """去除 Authorization 两端空白，并兼容 Bearer 令牌格式。"""
        value = (authorization or "").strip()
        if value.lower().startswith("bearer "):
            return value[7:].strip()
        return value

    @staticmethod
    def _set_token_cookie(
        response: Response | None,
        token: str,
        expires_at: datetime,
    ) -> None:
        """将令牌写入 HttpOnly Cookie，Cookie 有效期不超过令牌剩余时间。"""
        if response is None:
            return
        max_age = max(0, int((expires_at - datetime.now()).total_seconds()))
        response.set_cookie(
            key="token",
            value=token,
            max_age=max_age,
            httponly=False,
            samesite="lax",
            secure=False,
            path="/",
        )

    @staticmethod
    def _serialize_user(user: User) -> dict[str, object]:
        """转换除密码外的用户字段，避免将密码哈希暴露给调用方。"""
        return {
            "id": user.id,
            "username": user.username,
            "nickname": getattr(user, "nickname", None),
            "avatar": getattr(user, "avatar", None),
            "gender": getattr(user, "gender", None),
            "bio": getattr(user, "bio", None),
            "phone": getattr(user, "phone", None),
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }


def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    """提供一个使用请求级数据库会话的用户服务实例。"""
    return UserService(UserRepository(db))
