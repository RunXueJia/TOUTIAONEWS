from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.schemas.users import UserInfoResponse, UserLoginRequest, UserRegisterRequest, UserRegisterResponse
from app.services.users import (
    InvalidCredentialsError,
    TokenExpiredError,
    TokenNotFoundError,
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
        "注册成功后同时生成 7 天有效的用户认证令牌。"
        "所有响应均使用 HTTP 200；用户名重复和参数校验失败时，"
        "分别在响应体中返回 code=409 和 code=422。"
    ),
    response_description="返回新建用户的公开信息和认证令牌；业务错误通过响应体的 code 返回。",
    response_model=UserRegisterResponse,
    responses={
        200: {"description": "注册结果或包含业务错误码的响应体。"},
    },
)
async def register_user(
    payload: UserRegisterRequest,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> dict[str, object]:
    """注册用户，用户名重复时在响应体中返回 code=409。"""
    try:
        return await service.register(
            username=payload.username,
            password=payload.password,
            response=response,
        )
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc


@router.post(
    "/login",
    summary="用户登录",
    description=(
        "查询用户名并校验密码。登录成功时复用七日内有效的认证令牌，"
        "令牌不存在或已过期时创建新令牌。所有响应均使用 HTTP 200，"
        "认证失败和参数校验失败分别在响应体中返回 code=401 和 code=422。"
    ),
    response_description="返回与注册接口一致的认证令牌和用户公开信息；业务错误通过响应体的 code 返回。",
    response_model=UserRegisterResponse,
    responses={
        200: {"description": "登录结果或包含业务错误码的响应体。"},
    },
)
async def login_user(
    payload: UserLoginRequest,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> dict[str, object]:
    """登录用户并返回认证令牌与公开用户信息。"""
    try:
        return await service.login(
            username=payload.username,
            password=payload.password,
            response=response,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="用户名或密码错误") from exc


@router.get(
    "/info",
    summary="获取当前用户信息",
    description=(
        "读取请求头 Authorization 中的用户令牌，查询令牌并校验有效期后返回用户公开信息。"
        "令牌不存在时返回 code=401，令牌过期时返回 code=402；业务错误通过响应体返回，HTTP 状态统一为 200。"
    ),
    response_description="当前用户的公开信息，不包含密码和令牌。",
    response_model=UserInfoResponse,
    responses={
        200: {"description": "查询成功或包含业务错误码的响应体。"},
        401: {"description": "Authorization 令牌不存在或无效。"},
        402: {"description": "Authorization 令牌已过期，需要重新登录。"},
    },
)
async def get_user_info(
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
        description="用户认证令牌，支持直接传入令牌或 Bearer <token>。",
        examples=["Bearer example-token"],
    ),
    service: UserService = Depends(get_user_service),
) -> dict[str, object]:
    """读取 Authorization 令牌并返回当前用户信息。"""
    try:
        return await service.get_user_info(authorization)
    except TokenExpiredError as exc:
        raise HTTPException(status_code=402, detail="登录已过期") from exc
    except TokenNotFoundError as exc:
        raise HTTPException(status_code=401, detail="登录凭证无效") from exc
