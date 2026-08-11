#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""API 路由共享的 FastAPI 依赖项。"""

from typing import Annotated

from fastapi import Depends, Query
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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


Pagination = Annotated[PaginationParams, Depends(get_pagination)]

__all__ = ["Pagination", "PaginationParams", "get_pagination"]
