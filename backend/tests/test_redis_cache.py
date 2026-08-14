"""Redis 缓存读写封装的单元测试。"""

import asyncio

from app.db.redis import get_cache, set_cache


class FakeRedis:
    """在内存中模拟本次测试需要的 Redis get/set 行为。"""

    def __init__(self) -> None:
        """初始化缓存数据和每次写入记录。"""
        self.values: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """记录过期时间并保存序列化后的缓存内容。"""
        self.values[key] = value
        self.set_calls.append((key, value, ex))

    async def get(self, key: str) -> str | None:
        """返回指定键的模拟缓存内容。"""
        return self.values.get(key)


def test_redis_cache_round_trip_keeps_json_value_and_expiry() -> None:
    """缓存封装应使用 JSON 往返数据，并将指定过期时间传给 Redis。"""
    async def verify() -> None:
        redis_client = FakeRedis()
        value = {"items": [{"id": 1, "title": "新闻"}], "total": 1}

        await set_cache(redis_client, "news:list:1", value, expire_seconds=60)

        assert await get_cache(redis_client, "news:list:1") == value
        assert redis_client.set_calls == [
            ("news:list:1", '{"items":[{"id":1,"title":"新闻"}],"total":1}', 60)
        ]

    asyncio.run(verify())


def test_redis_cache_returns_none_for_missing_key_and_allows_persistent_cache() -> None:
    """未命中应返回空，且 None 有效期应写入永久缓存。"""
    async def verify() -> None:
        redis_client = FakeRedis()

        assert await get_cache(redis_client, "missing") is None
        await set_cache(redis_client, "news:categories", ["国内"], expire_seconds=None)

        assert await get_cache(redis_client, "news:categories") == ["国内"]
        assert redis_client.set_calls[0][2] is None

    asyncio.run(verify())


def test_redis_cache_rejects_invalid_keys_expiry_and_values() -> None:
    """缓存封装应在写入前拒绝无效参数，避免产生不可控缓存。"""
    async def verify() -> None:
        redis_client = FakeRedis()

        for key in ("", "   ", 1):
            try:
                await set_cache(redis_client, key, {"id": 1})
            except ValueError:
                continue
            raise AssertionError("空缓存键必须被拒绝")

        for expire_seconds in (0, -1, True, 1.5):
            try:
                await set_cache(redis_client, "news:list", {"id": 1}, expire_seconds=expire_seconds)
            except ValueError:
                continue
            raise AssertionError("无效缓存有效期必须被拒绝")

        try:
            await set_cache(redis_client, "news:list", {"ids": {1, 2}})
        except TypeError:
            pass
        else:
            raise AssertionError("不可 JSON 序列化的缓存值必须被拒绝")

    asyncio.run(verify())


def test_redis_cache_rejects_corrupted_cached_json() -> None:
    """读取到非 JSON 缓存时应明确报错，避免向业务层返回错误类型。"""
    async def verify() -> None:
        redis_client = FakeRedis()
        redis_client.values["broken"] = "not-json"

        try:
            await get_cache(redis_client, "broken")
        except ValueError:
            return
        raise AssertionError("损坏的 JSON 缓存必须被拒绝")

    asyncio.run(verify())
