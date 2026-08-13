"""收藏模块的 API 路由定义。"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import CurrentUser, get_optional_current_user
from app.models.users import User
from app.schemas.favorite import FavoriteAddRequest, FavoriteAddResponse, FavoriteCheckResponse
from app.services.favorite import (
    FavoriteAlreadyExistsError,
    FavoriteService,
    get_favorite_service,
)


router = APIRouter(
    prefix="/favorite",
    tags=["favorite"],
)


@router.get(
    "/check",
    summary="查询新闻收藏状态",
    description=(
        "根据 newsId 查询当前用户是否已收藏指定新闻。"
        "未携带登录信息、登录信息无效或已过期时不报错，统一返回未收藏。"
    ),
    response_description="返回指定新闻相对于当前用户的收藏状态。",
    response_model=FavoriteCheckResponse,
    responses={
        200: {"description": "查询成功或包含参数校验错误码的响应体。"},
        422: {"description": "newsId 参数不合法。"},
    },
)
async def check_news_favorite(
    news_id: int = Query(
        ...,
        alias="newsId",
        ge=1,
        description="需要查询收藏状态的新闻 ID。",
        examples=[1],
    ),
    current_user: User | None = Depends(get_optional_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> dict[str, bool]:
    """查询指定新闻是否已被当前登录用户收藏，匿名访问返回未收藏。"""
    return await service.is_news_favorited(
        user_id=current_user.id if current_user is not None else None,
        news_id=news_id,
    )


@router.post(
    "/add",
    summary="新增新闻收藏",
    description=(
        "校验 Authorization 登录凭证后，按当前用户和 newsId 创建收藏记录。"
        "同一用户重复收藏同一新闻时，响应体返回 code=409 和“已经收藏”；"
        "所有响应的 HTTP 状态均为 200。"
    ),
    response_description="新增的收藏记录；业务错误通过响应体的 code 返回。",
    response_model=FavoriteAddResponse,
    responses={
        200: {"description": "收藏成功或包含业务错误码的响应体。"},
        401: {"description": "Authorization 令牌不存在或无效。"},
        402: {"description": "Authorization 令牌已过期，需要重新登录。"},
        409: {"description": "当前用户已收藏该新闻。"},
    },
)
async def add_news_favorite(
    payload: FavoriteAddRequest,
    current_user: CurrentUser,
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteAddResponse:
    """为当前登录用户新增新闻收藏，重复收藏时返回业务冲突响应。"""
    try:
        favorite = await service.add_news_favorite(
            user_id=current_user.id,
            news_id=payload.news_id,
        )
    except FavoriteAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="已经收藏") from exc

    return FavoriteAddResponse.model_validate(favorite)
