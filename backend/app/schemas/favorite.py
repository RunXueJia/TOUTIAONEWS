"""收藏模块的 Pydantic 请求与响应模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
