"""用户领域 ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.mysql import ENUM, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """注册用户表，对应数据库中的 ``user`` 表。"""

    __tablename__ = "user"

    __table_args__ = (
        UniqueConstraint("username", name="username_UNIQUE"),
        UniqueConstraint("phone", name="phone_UNIQUE"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(
        ENUM("male", "female", "unknown"),
        nullable=True,
        server_default="unknown",
    )
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserToken(Base):
    """用户认证令牌表，对应数据库中的 ``user_token`` 表。"""

    __tablename__ = "user_token"

    __table_args__ = (
        UniqueConstraint("token", name="token_UNIQUE"),
        Index("fk_user_token_user_idx", "user_id"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
