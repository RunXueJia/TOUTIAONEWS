"""异步 SQLAlchemy 数据库配置。"""

import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set in the environment or .env file.")

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """为每次请求提供一个数据库会话，并在结束后关闭。"""
    async with AsyncSessionLocal() as db:
        yield db
