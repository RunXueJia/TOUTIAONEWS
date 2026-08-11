from fastapi import APIRouter

from app.schemas.users import UserListPlaceholderResponse


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/get_user_list",
    summary="获取用户列表占位响应",
    description="返回当前用户模块的占位响应内容。",
    response_description="用户模块的占位状态消息。",
    response_model=UserListPlaceholderResponse,
)
async def get_user_list() -> UserListPlaceholderResponse:
    """返回用户模块的占位响应。"""
    return {"message": "Users router"}
