"""用户注册接口及服务的回归测试。"""

import asyncio
from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services.users import (
    UserService,
    UsernameAlreadyExistsError,
    get_user_service,
)
from app.utils.password import verify_password
from main import app


class FakeUserRepository:
    """为注册测试提供内存用户仓储。"""

    def __init__(self, existing_username: str | None = None) -> None:
        """可选地预置一个已存在的用户名。"""
        self.existing_username = existing_username
        self.received_password: str | None = None

    async def get_by_username(self, username: str) -> SimpleNamespace | None:
        """模拟按用户名查询操作。"""
        if username == self.existing_username:
            return SimpleNamespace(username=username)
        return None

    async def create_user(self, *, username: str, password: str) -> SimpleNamespace:
        """记录写入值并返回带有时间戳的用户。"""
        self.received_password = password
        timestamp = datetime(2026, 8, 11, 9, 0)
        return SimpleNamespace(
            id=1,
            username=username,
            password=password,
            created_at=timestamp,
            updated_at=timestamp,
        )


def test_user_service_hashes_password_and_returns_public_fields() -> None:
    """服务层应保存密码哈希，且响应不暴露密码字段。"""
    async def verify() -> None:
        repository = FakeUserRepository()
        result = await UserService(repository).register(
            username="zhangsan",
            password="example-password",
        )

        assert repository.received_password is not None
        assert repository.received_password != "example-password"
        assert verify_password("example-password", repository.received_password)
        assert result["userInfo"]["username"] == "zhangsan"
        assert "password" not in result["userInfo"]

    asyncio.run(verify())


def test_register_rejects_existing_username() -> None:
    """服务层应在创建前检查用户名是否已存在。"""
    async def verify() -> None:
        service = UserService(FakeUserRepository(existing_username="zhangsan"))
        try:
            await service.register(username="zhangsan", password="example-password")
        except UsernameAlreadyExistsError:
            return
        raise AssertionError("重复用户名必须被拒绝")

    asyncio.run(verify())


def test_register_endpoint_wraps_user_info_and_validates_strings() -> None:
    """接口应返回 userInfo，并拒绝非字符串的请求字段。"""
    async def fake_service_dependency() -> UserService:
        """为接口测试注入独立的用户服务。"""
        return UserService(FakeUserRepository())

    app.dependency_overrides[get_user_service] = fake_service_dependency
    try:
        client = TestClient(app)
        success_response = client.post(
            "/api/user/register",
            json={"username": "zhangsan", "password": "example-password"},
        )
        invalid_response = client.post(
            "/api/user/register",
            json={"username": 123, "password": "example-password"},
        )
    finally:
        app.dependency_overrides.pop(get_user_service, None)

    assert success_response.status_code == 200
    assert success_response.json()["data"]["userInfo"]["username"] == "zhangsan"
    assert "password" not in success_response.json()["data"]["userInfo"]
    assert invalid_response.status_code == 200
    assert invalid_response.json()["code"] == 422
