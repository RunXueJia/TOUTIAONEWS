#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""API 路由共享的 FastAPI 依赖项。"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from app.models.users import User
from app.services.users import (
    TokenExpiredError,
    TokenNotFoundError,
    UserService,
    get_user_service,
)


class PaginationParams(BaseModel):
    """列表接口使用的已校验分页参数。"""

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(
        default=10,
        alias="pageSize",
        validation_alias=AliasChoices("pageSize", "page_size"),
        ge=1,
        le=100,
        description="每页记录数，范围 1 到 100",
    )

    @property
    def offset(self) -> int:
        """返回当前页对应的 SQL 偏移量。"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """返回当前页对应的 SQL 限制条数。"""
        return self.page_size


def get_pagination(
    page: Annotated[
        int,
        Query(ge=1, description="页码，从 1 开始"),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            alias="pageSize",
            validation_alias=AliasChoices("pageSize", "page_size"),
            ge=1,
            le=100,
            description="每页记录数，范围 1 到 100",
        ),
    ] = 10,
) -> PaginationParams:
    """根据查询参数构造并校验分页参数。"""
    return PaginationParams(page=page, page_size=page_size)


async def get_current_user(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
        description="用户认证令牌，支持直接传入令牌或 Bearer <token>。",
        examples=["Bearer example-token"],
    ),
    service: UserService = Depends(get_user_service),
) -> User:
    """校验请求令牌并返回当前用户，供所有需要登录态的路由声明依赖。"""
    try:
        return await service.validate_token(authorization)
    except TokenExpiredError as exc:
        raise HTTPException(status_code=402, detail="登录已过期") from exc
    except TokenNotFoundError as exc:
        raise HTTPException(status_code=401, detail="登录凭证无效") from exc


async def get_optional_current_user(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
        description="可选的用户认证令牌；未登录或令牌无效时按匿名用户处理。",
        examples=["Bearer example-token"],
    ),
    service: UserService = Depends(get_user_service),
) -> User | None:
    """尝试解析当前用户；未登录、令牌无效或过期时返回空而不产生认证错误。"""
    try:
        return await service.validate_token(authorization)
    except (TokenExpiredError, TokenNotFoundError):
        return None


Pagination = Annotated[PaginationParams, Depends(get_pagination)]
CurrentUser = Annotated[User, Depends(get_current_user)]

__all__ = [
    "CurrentUser",
    "Pagination",
    "PaginationParams",
    "get_current_user",
    "get_optional_current_user",
    "get_pagination",
]
