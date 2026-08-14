"""异步 Redis 连接与 FastAPI 依赖。"""

import json
import os
from typing import Any

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


async def set_cache(
    redis_client: Redis,
    key: str,
    value: Any,
    *,
    expire_seconds: int | None = 300,
) -> None:
    """将可 JSON 序列化的数据写入 Redis 缓存。

    参数 ``expire_seconds`` 为缓存有效期（秒）；传入 ``None`` 时不过期。
    键为空、过期时间不合法或数据不可序列化时抛出 ``ValueError`` 或 ``TypeError``。
    """
    _validate_cache_key(key)
    _validate_expire_seconds(expire_seconds)

    try:
        serialized_value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise TypeError("Redis 缓存值必须是可 JSON 序列化的数据。") from exc

    if expire_seconds is None:
        await redis_client.set(key, serialized_value)
        return

    await redis_client.set(key, serialized_value, ex=expire_seconds)


async def get_cache(redis_client: Redis, key: str) -> Any | None:
    """读取并反序列化 Redis 缓存；键不存在时返回 ``None``。

    缓存内容不是合法 JSON 时抛出 ``ValueError``，以便调用方发现并清理异常缓存。
    """
    _validate_cache_key(key)

    cached_value = await redis_client.get(key)
    if cached_value is None:
        return None

    try:
        return json.loads(cached_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Redis 缓存键 {key!r} 的内容不是合法 JSON。") from exc


def _validate_cache_key(key: str) -> None:
    """校验缓存键为非空字符串，避免错误地读写无意义的 Redis 键。"""
    if not isinstance(key, str) or not key.strip():
        raise ValueError("Redis 缓存键必须是非空字符串。")


def _validate_expire_seconds(expire_seconds: int | None) -> None:
    """校验缓存有效期；空值表示永久缓存，正整数表示秒数。"""
    if expire_seconds is None:
        return
    if isinstance(expire_seconds, bool) or not isinstance(expire_seconds, int) or expire_seconds <= 0:
        raise ValueError("Redis 缓存有效期必须是正整数秒或 None。")


async def close_redis_client(redis_client: Redis) -> None:
    """关闭 Redis 客户端及其连接池，释放应用退出时持有的连接。"""
    await redis_client.aclose()


def get_redis(request: Request) -> Redis:
    """返回当前应用生命周期内的 Redis 客户端，供路由和服务层依赖注入。"""
    return request.app.state.redis
