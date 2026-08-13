"""浏览历史模块的 Pydantic 请求与响应模型。"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.news import NewsItemResponse


class HistoryAddRequest(BaseModel):
    """用户新增新闻浏览历史时提交的请求体。"""

    model_config = ConfigDict(extra="forbid")

    news_id: int = Field(
        ...,
        alias="newsId",
        strict=True,
        ge=1,
        description="需要记录浏览历史的新闻 ID。",
        examples=[1],
    )


class HistoryAddResponse(BaseModel):
    """新增成功后返回的浏览历史记录。"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int = Field(description="浏览历史记录 ID。", examples=[1])
    user_id: int = Field(alias="userId", description="浏览用户 ID。", examples=[1])
    news_id: int = Field(alias="newsId", description="被浏览的新闻 ID。", examples=[1])
    view_time: datetime = Field(
        alias="viewTime",
        description="新闻浏览时间。",
    )


class HistoryListResponse(BaseModel):
    """当前用户浏览历史新闻列表的分页结构。"""

    list: List[NewsItemResponse] = Field(description="当前页浏览历史新闻")
    total: int = Field(ge=0, description="用户浏览过且仍存在的新闻总数")
    has_more: bool = Field(alias="hasMore", description="是否还有下一页浏览历史")


class HistoryDeleteResponse(BaseModel):
    """删除浏览历史接口的统一响应结构。"""

    code: int = Field(description="业务状态码；成功为 200。", examples=[200])
    message: str = Field(description="操作结果说明。", examples=["删除浏览记录成功"])
    data: None = Field(default=None, description="删除操作不返回业务数据。")
