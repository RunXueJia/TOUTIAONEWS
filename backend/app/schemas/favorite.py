"""收藏模块的 Pydantic 响应模型。"""

from pydantic import BaseModel, Field


class FavoriteCheckResponse(BaseModel):
    """指定新闻相对于当前用户的收藏状态。"""

    is_favorite: bool = Field(
        alias="isFavorite",
        description="当前登录用户是否已收藏该新闻；未登录时始终为 false。",
        examples=[True],
    )
