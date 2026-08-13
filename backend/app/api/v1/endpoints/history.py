"""浏览历史模块的路由入口。"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/history",
    tags=["history"],
    dependencies=[Depends(get_current_user)],
)
