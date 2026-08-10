from fastapi import APIRouter


router = APIRouter(prefix="/news", tags=["news"])


@router.get("/get_news_list")
async def get_news_list():
    """Return the news module placeholder response."""
    return {"message": "News router"}
