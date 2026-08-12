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


class UserLoginRequest(BaseModel):
    """用户登录时提交的用户名和密码。"""

    username: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=50,
        description="已注册的用户名。",
        examples=["zhangsan"],
    )
    password: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=128,
        description="登录密码，不会在响应中返回。",
        examples=["example-password"],
    )


class UserUpdateRequest(BaseModel):
    """当前用户可修改的非账号资料字段，未提交字段不会被更新。"""

    model_config = ConfigDict(extra="forbid")

    nickname: str | None = Field(
        default=None,
        max_length=50,
        description="昵称；显式传 null 可清空。",
        examples=["张三"],
    )
    avatar: str | None = Field(
        default=None,
        max_length=255,
        description="头像 URL；显式传 null 可清空。",
    )
    gender: str | None = Field(
        default=None,
        max_length=10,
        description="性别；显式传 null 可清空。",
        examples=["male"],
    )
    bio: str | None = Field(
        default=None,
        max_length=500,
        description="个人简介；显式传 null 可清空。",
    )


class UserPasswordUpdateRequest(BaseModel):
    """当前用户修改密码时提交的旧密码和新密码。"""

    model_config = ConfigDict(extra="forbid")

    new_password: str = Field(
        ...,
        alias="newPassword",
        strict=True,
        min_length=1,
        max_length=128,
        description="新密码，不会在响应中返回。",
        examples=["new-example-password"],
    )
    old_password: str = Field(
        ...,
        alias="oldPassword",
        strict=True,
        min_length=1,
        max_length=128,
        description="当前密码，用于校验身份，不会在响应中返回。",
        examples=["old-example-password"],
    )


class UserInfoResponse(BaseModel):
    """可安全返回给客户端的用户公开信息（不包含密码）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="用户自增 ID", examples=[1])
    username: str = Field(description="用户唯一名称", examples=["zhangsan"])
    nickname: str | None = Field(default=None, description="用户昵称", examples=["张三"])
    avatar: str | None = Field(default=None, description="头像 URL")
    gender: str | None = Field(default=None, description="性别：male、female 或 unknown", examples=["unknown"])
    bio: str | None = Field(default=None, description="个人简介", examples=["这个人很懒，什么都没留下"])
    phone: str | None = Field(default=None, description="手机号")
    created_at: datetime = Field(description="用户创建时间")
    updated_at: datetime = Field(description="用户最后更新时间")


class UserRegisterResponse(BaseModel):
    """注册接口的业务数据结构。"""

    token: str = Field(description="用户认证令牌。")
    user_info: UserInfoResponse = Field(
        alias="userInfo",
        description="新建用户的公开信息，不包含密码。",
    )
