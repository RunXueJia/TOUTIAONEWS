"""用户 API 模块的 Pydantic 请求与响应模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    """用户注册时提交的用户名和密码。"""

    username: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=50,
        description="唯一用户名。",
        examples=["zhangsan"],
    )
    password: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=128,
        description="明文密码，仅用于本次注册，不会在响应中返回。",
        examples=["example-password"],
    )


class UserInfoResponse(BaseModel):
    """注册成功后可安全返回的用户信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="用户自增 ID", examples=[1])
    username: str = Field(description="用户唯一名称", examples=["zhangsan"])
    created_at: datetime = Field(description="用户创建时间")
    updated_at: datetime = Field(description="用户最后更新时间")


class UserRegisterResponse(BaseModel):
    """注册接口的业务数据结构。"""

    user_info: UserInfoResponse = Field(
        alias="userInfo",
        description="新建用户的公开信息，不包含密码。",
    )
