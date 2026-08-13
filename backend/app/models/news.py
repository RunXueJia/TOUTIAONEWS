"""新闻领域 ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class News(Base):
    """已发布的新闻文章。"""

    __tablename__ = "news"

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str | None] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(50))
    category_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    views: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, server_default="0")
    publish_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("fk_news_category_idx", "category_id"),
        Index("idx_publish_time", publish_time.desc()),
    )


class NewsCategory(Base):
    """用于给新闻文章分类的类别。"""

    __tablename__ = "news_category"

    __table_args__ = (
        UniqueConstraint("name", name="name_UNIQUE"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(INTEGER, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Favorite(Base):
    """用户收藏新闻的关联记录，对应 ``favorite`` 表。"""

    __tablename__ = "favorite"

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="user_news_unique"),
        Index("fk_favorite_user_idx", "user_id"),
        Index("fk_favorite_news_idx", "news_id"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    news_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


class RelatedNews(Base):
    """新闻推荐系统中的相关新闻关联记录，对应 ``related_news`` 表。"""

    __tablename__ = "related_news"

    __table_args__ = (
        UniqueConstraint("news_id", "related_news_id", name="news_related_unique"),
        Index("fk_related_news_news_idx", "news_id"),
        Index("fk_related_news_related_idx", "related_news_id"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    related_news_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class History(Base):
    """用户浏览新闻的历史记录，对应 ``history`` 表。"""

    __tablename__ = "history"

    __table_args__ = (
        Index("fk_history_user_idx", "user_id"),
        Index("fk_history_news_idx", "news_id"),
        Index("idx_view_time", "view_time"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    news_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    view_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class AIChat(Base):
    """用户与 AI 的聊天记录，对应 ``ai_chat`` 表。"""

    __tablename__ = "ai_chat"

    __table_args__ = (
        Index("fk_ai_chat_user_idx", "user_id"),
        Index("idx_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
