"""SQLAlchemy 模型包，集中导入全部实体以完成元数据注册。"""

from app.models.news import AIChat, Favorite, History, News, NewsCategory, RelatedNews
from app.models.users import User, UserToken

__all__ = [
    "AIChat",
    "Favorite",
    "History",
    "News",
    "NewsCategory",
    "RelatedNews",
    "User",
    "UserToken",
]
