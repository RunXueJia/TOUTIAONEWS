"""异步 Redis 连接与 FastAPI 依赖。"""

import os

from dotenv import load_dotenv
from fastapi import Request
from redis.asyncio import Redis


load_dotenv()


def create_redis_client() -> Redis:
    """根据环境变量创建 Redis 异步客户端，连接将在首次命令或健康检查时建立。"""
    host = os.getenv("REDIS_HOST", "").strip()
    if not host:
        raise RuntimeError("请先在 .env 中配置 REDIS_HOST。")

    return Redis(
        host=host,
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        username=os.getenv("REDIS_USERNAME") or None,
        password=os.getenv("REDIS_PASSWORD") or None,
        ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
        decode_responses=True,
    )


async def close_redis_client(redis_client: Redis) -> None:
    """关闭 Redis 客户端及其连接池，释放应用退出时持有的连接。"""
    await redis_client.aclose()


def get_redis(request: Request) -> Redis:
    """返回当前应用生命周期内的 Redis 客户端，供路由和服务层依赖注入。"""
    return request.app.state.redis
