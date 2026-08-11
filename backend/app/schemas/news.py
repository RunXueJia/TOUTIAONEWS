"""新闻 API 模块的 Pydantic 响应模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field


class NewsItemResponse(BaseModel):
    """新闻文章对外返回的字段。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="新闻文章 ID", examples=[1])
    publish_time: datetime = Field(description="文章发布时间")
    created_at: datetime = Field(description="文章创建时间")
    updated_at: datetime = Field(description="文章最后更新时间")
    category: dict[str, Any] | None = Field(
        default=None,
        description="可选的扩展分类信息",
    )
    title: str = Field(description="文章标题", examples=["示例新闻标题"])
    description: str | None = Field(default=None, description="文章摘要")
    content: str = Field(description="文章正文")
    image: str | None = Field(default=None, description="文章封面图地址")
    author: str | None = Field(default=None, description="文章作者")
    category_id: int = Field(description="分类 ID", examples=[1])
    views: int = Field(ge=0, description="当前文章浏览量")


class NewsListResponse(BaseModel):
    """统一响应包装前的分页新闻列表结构。"""

    list: List[NewsItemResponse] = Field(description="当前页新闻记录")
    total: int = Field(ge=0, description="符合条件的总记录数")
    has_more: bool = Field(
        alias="hasMore",
        description="是否还有下一页数据",
    )


class NewsDetailResponse(NewsItemResponse):
    """包含推荐文章的新闻详情结构。"""

    related_news: list[NewsItemResponse] = Field(
        alias="relatedNews",
        description="同分类的相关文章",
    )


class NewsCategoryResponse(BaseModel):
    """新闻分类对外返回的字段。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="分类 ID", examples=[1])
    created_at: datetime = Field(description="分类创建时间")
    updated_at: datetime = Field(description="分类最后更新时间")
    name: str = Field(description="分类展示名称", examples=["科技"])
    sort_order: int = Field(description="展示顺序，值越小越靠前")
