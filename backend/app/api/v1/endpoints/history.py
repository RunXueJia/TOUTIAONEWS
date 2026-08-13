"""浏览历史模块的 API 路由定义。"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.core.dependencies import CurrentUser, get_optional_current_user
from app.models.users import User
from app.schemas.history import (
    HistoryAddRequest,
    HistoryAddResponse,
    HistoryDeleteResponse,
    HistoryListResponse,
)
from app.services.history import (
    HistoryNewsNotFoundError,
    HistoryNotFoundError,
    HistoryService,
    get_history_service,
)


router = APIRouter(prefix="/history", tags=["history"])


@router.post(
    "/add",
    summary="新增新闻浏览历史",
    description=(
        "登录用户提交 newsId 后记录浏览历史；同一用户重复浏览同一新闻时仅更新浏览时间。"
        "未登录、登录令牌无效或已过期时不报错，直接返回成功且不写入浏览历史。"
    ),
    response_description="新增的浏览历史记录；匿名访问时 data 为 null。",
    response_model=HistoryAddResponse | None,
    responses={
        200: {"description": "记录成功或匿名访问时的统一成功响应。"},
        422: {"description": "newsId 必须为正整数。"},
    },
)
async def add_history(
    payload: HistoryAddRequest,
    current_user: User | None = Depends(get_optional_current_user),
    service: HistoryService = Depends(get_history_service),
) -> HistoryAddResponse | None:
    """记录登录用户的新闻浏览时间；匿名用户跳过持久化并保持请求成功。"""
    if current_user is None:
        return None

    history = await service.add_history(
        user_id=current_user.id,
        news_id=payload.news_id,
    )
    return HistoryAddResponse.model_validate(history)


@router.delete(
    "/delete/{id}",
    summary="删除新闻浏览记录",
    description=(
        "校验当前登录用户、新闻是否存在以及该用户是否浏览过该新闻，"
        "满足条件后删除对应的浏览历史记录。"
    ),
    response_description="删除结果；业务错误通过响应体的 code 返回。",
    response_model=HistoryDeleteResponse,
    responses={
        200: {"description": "删除成功或包含业务错误码的响应体。"},
        401: {"description": "Authorization 令牌不存在或无效。"},
        402: {"description": "Authorization 令牌已过期，需要重新登录。"},
        404: {"description": "新闻不存在，或当前用户没有该新闻的浏览记录。"},
        422: {"description": "新闻 ID 必须为正整数。"},
    },
)
async def delete_history(
    current_user: CurrentUser,
    news_id: int = Path(
        ...,
        alias="id",
        ge=1,
        description="需要删除浏览记录的新闻 ID。",
        examples=[1],
    ),
    service: HistoryService = Depends(get_history_service),
) -> dict[str, object]:
    """删除当前登录用户指定新闻的浏览记录。"""
    try:
        await service.delete_history(user_id=current_user.id, news_id=news_id)
    except HistoryNewsNotFoundError as exc:
        raise HTTPException(status_code=404, detail="新闻不存在") from exc
    except HistoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail="尚未浏览该新闻") from exc

    return {"code": 200, "message": "删除浏览记录成功", "data": None}


@router.delete(
    "/clear",
    summary="清空浏览历史",
    description="校验当前登录用户及用户身份后，删除该用户的全部新闻浏览历史记录。",
    response_description="清空结果；业务错误通过响应体的 code 返回。",
    response_model=HistoryDeleteResponse,
    responses={
        200: {"description": "清空成功，或包含业务错误码的响应体。"},
        401: {"description": "Authorization 令牌不存在或无效。"},
        402: {"description": "Authorization 令牌已过期，需要重新登录。"},
    },
)
async def clear_history(
    current_user: CurrentUser,
    service: HistoryService = Depends(get_history_service),
) -> dict[str, object]:
    """清空当前登录用户的全部新闻浏览历史记录。"""
    await service.clear_history(user_id=current_user.id)
    return {"code": 200, "message": "清空浏览历史成功", "data": None}


@router.get(
    "/list",
    summary="获取浏览历史列表",
    description="校验当前登录用户身份，联表查询其浏览过的新闻并返回分页结果。",
    response_description="当前登录用户浏览历史新闻的分页列表。",
    response_model=HistoryListResponse,
    responses={
        401: {"description": "Authorization 令牌不存在或无效。"},
        402: {"description": "Authorization 令牌已过期，需要重新登录。"},
        422: {"description": "分页参数不合法。"},
    },
)
async def get_history_list(
    current_user: CurrentUser,
    page: int = Query(1, ge=1, description="页码，从 1 开始，默认值为 1。"),
    page_size: int = Query(
        10,
        alias="pageSize",
        ge=1,
        le=100,
        description="每页浏览历史新闻数量，默认 10，最大 100。",
    ),
    service: HistoryService = Depends(get_history_service),
) -> dict[str, object]:
    """返回当前登录用户浏览历史中的新闻分页列表。"""
    return await service.list_history_news(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
