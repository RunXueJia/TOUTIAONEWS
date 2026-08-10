#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reusable FastAPI dependencies shared by API endpoints."""

from typing import Annotated

from fastapi import Depends, Query
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    """Validated pagination parameters for list endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(
        default=10,
        alias="pageSize",
        validation_alias=AliasChoices("pageSize", "page_size"),
        ge=1,
        le=100,
        description="Number of records per page (1-100)",
    )

    @property
    def offset(self) -> int:
        """Return the SQL offset for the requested page."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return the SQL limit for the requested page."""
        return self.page_size


def get_pagination(
    page: Annotated[
        int,
        Query(ge=1, description="Page number starting at 1"),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            alias="pageSize",
            validation_alias=AliasChoices("pageSize", "page_size"),
            ge=1,
            le=100,
            description="Number of records per page (1-100)",
        ),
    ] = 10,
) -> PaginationParams:
    """Build validated pagination parameters from query string values."""
    return PaginationParams(page=page, page_size=page_size)


Pagination = Annotated[PaginationParams, Depends(get_pagination)]

__all__ = ["Pagination", "PaginationParams", "get_pagination"]
