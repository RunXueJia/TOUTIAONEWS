"""收藏模块的 Pydantic 请求与响应模型。"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.news import NewsItemResponse


class FavoriteAddRequest(BaseModel):
    """用户新增新闻收藏时提交的请求体。"""

    model_config = ConfigDict(extra="forbid")

    news_id: int = Field(
        ...,
        alias="newsId",
        strict=True,
        ge=1,
        description="需要收藏的新闻 ID。",
        examples=[1],
    )


class FavoriteAddResponse(BaseModel):
    """新增成功后返回的收藏记录。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(description="收藏记录 ID。", examples=[1])
    user_id: int = Field(alias="userId", description="收藏用户 ID。", examples=[1])
    news_id: int = Field(alias="newsId", description="被收藏的新闻 ID。", examples=[1])
    created_at: datetime = Field(description="收藏创建时间。")


class FavoriteCheckResponse(BaseModel):
    """指定新闻相对于当前用户的收藏状态。"""

    is_favorite: bool = Field(
        alias="isFavorite",
        description="当前登录用户是否已收藏该新闻；未登录时始终为 false。",
        examples=[True],
    )


class FavoriteRemoveResponse(BaseModel):
    """取消新闻收藏接口的统一响应结构。"""

    code: int = Field(description="业务状态码；成功为 200。", examples=[200])
    message: str = Field(description="操作结果说明。", examples=["取消收藏成功"])
    data: None = Field(default=None, description="取消收藏不返回业务数据。")


class FavoriteListResponse(BaseModel):
    """当前用户收藏新闻列表的分页结构。"""

    list: List[NewsItemResponse] = Field(description="当前页收藏新闻")
    total: int = Field(ge=0, description="用户收藏且仍存在的新闻总数")
    has_more: bool = Field(alias="hasMore", description="是否还有下一页收藏新闻")
