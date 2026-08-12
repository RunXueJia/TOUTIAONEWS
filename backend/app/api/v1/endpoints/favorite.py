"""收藏模块的 API 路由定义。"""

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_optional_current_user
from app.models.users import User
from app.schemas.favorite import FavoriteCheckResponse
from app.services.favorite import FavoriteService, get_favorite_service


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
