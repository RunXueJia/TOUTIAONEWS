from fastapi import APIRouter


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/get_user_list")
async def get_user_list():
    """Return the users module placeholder response."""
    return {"message": "Users router"}
