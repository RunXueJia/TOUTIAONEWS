from fastapi import APIRouter, Depends, HTTPException

from app.schemas.users import UserRegisterRequest, UserRegisterResponse
from app.services.users import (
    UserService,
    UsernameAlreadyExistsError,
    get_user_service,
)


router = APIRouter(prefix="/user", tags=["user"])


@router.post(
    "/register",
    summary="注册用户",
    description=(
        "使用唯一用户名创建用户，并以 bcrypt 哈希后的密码写入数据库。"
        "所有响应均使用 HTTP 200；用户名重复和参数校验失败时，"
        "分别在响应体中返回 code=409 和 code=422。"
    ),
    response_description="新建用户的公开信息，不包含密码；业务错误通过响应体的 code 返回。",
    response_model=UserRegisterResponse,
    responses={
        200: {"description": "注册结果或包含业务错误码的响应体。"},
    },
)
async def register_user(
    payload: UserRegisterRequest,
    service: UserService = Depends(get_user_service),
) -> dict[str, object]:
    """注册用户，用户名重复时在响应体中返回 code=409。"""
    try:
        return await service.register(username=payload.username, password=payload.password)
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc
