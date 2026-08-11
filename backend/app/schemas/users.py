"""用户 API 模块的 Pydantic 响应模型。"""

from pydantic import BaseModel, Field


class UserListPlaceholderResponse(BaseModel):
    """用户列表占位接口的临时响应结构。"""

    message: str = Field(
        description="用户模块的占位状态消息",
        examples=["Users router"],
    )
