"""Pydantic 模型包。"""

from app.schemas.news import (
    NewsCategoryResponse,
    NewsDetailResponse,
    NewsItemResponse,
    NewsListResponse,
)
from app.schemas.history import (
    HistoryAddRequest,
    HistoryAddResponse,
    HistoryDeleteResponse,
    HistoryListResponse,
)
from app.schemas.users import (
    UserInfoResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
    UserUpdateRequest,
)

__all__ = [
    "NewsCategoryResponse",
    "NewsDetailResponse",
    "NewsItemResponse",
    "NewsListResponse",
    "HistoryAddRequest",
    "HistoryAddResponse",
    "HistoryDeleteResponse",
    "HistoryListResponse",
    "UserInfoResponse",
    "UserLoginRequest",
    "UserRegisterRequest",
    "UserRegisterResponse",
    "UserUpdateRequest",
]
