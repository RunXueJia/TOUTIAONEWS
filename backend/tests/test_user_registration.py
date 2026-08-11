"""用户注册接口及服务的回归测试。"""

import asyncio
from datetime import datetime
from types import SimpleNamespace

from fastapi import Response
from fastapi.testclient import TestClient

from app.services.users import (
    InvalidCredentialsError,
    UserService,
    UsernameAlreadyExistsError,
    get_user_service,
)
from app.utils.password import hash_password, verify_password
from main import app


class FakeUserRepository:
    """为注册测试提供内存用户仓储。"""

    def __init__(self, existing_username: str | None = None) -> None:
        """可选地预置一个已存在的用户名。"""
        self.existing_username = existing_username
        self.received_password: str | None = None
        self.received_token_request: dict[str, object] | None = None

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

    async def create_or_update_token(
        self,
        *,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> SimpleNamespace:
        """模拟用户令牌的创建或更新操作。"""
        self.received_token_request = {
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at,
        }
        return SimpleNamespace(token=token)


def test_user_service_hashes_password_and_returns_public_fields() -> None:
    """服务层应保存密码哈希，且响应不暴露密码字段。"""
    async def verify() -> None:
        repository = FakeUserRepository()
        response = Response()
        result = await UserService(repository).register(
            username="zhangsan",
            password="example-password",
            response=response,
        )

        assert repository.received_password is not None
        assert repository.received_password != "example-password"
        assert verify_password("example-password", repository.received_password)
        assert result["userInfo"]["username"] == "zhangsan"
        assert isinstance(result["token"], str)
        assert repository.received_token_request is not None
        assert repository.received_token_request["user_id"] == 1
        assert f'token="Bearer {result["token"]}"' in response.headers["set-cookie"]
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


class FakeLoginRepository:
    """为登录测试提供带密码和令牌状态的内存用户仓储。"""

    def __init__(self, token: SimpleNamespace | None = None) -> None:
        """初始化一个固定用户及可选的已有令牌。"""
        timestamp = datetime(2026, 8, 11, 9, 0)
        self.user = SimpleNamespace(
            id=1,
            username="zhangsan",
            password=hash_password("example-password"),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.token = token
        self.updated_token: SimpleNamespace | None = None

    async def get_by_username(self, username: str) -> SimpleNamespace | None:
        """按用户名返回测试用户。"""
        return self.user if username == self.user.username else None

    async def get_token_by_user_id(self, user_id: int) -> SimpleNamespace | None:
        """返回测试用户当前令牌。"""
        return self.token if user_id == self.user.id else None

    async def create_or_update_token(
        self,
        *,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> SimpleNamespace:
        """记录登录时创建或刷新的令牌。"""
        self.updated_token = SimpleNamespace(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.token = self.updated_token
        return self.updated_token


def test_user_login_reuses_valid_token() -> None:
    """登录成功时应校验密码并复用未过期令牌。"""
    async def verify() -> None:
        repository = FakeLoginRepository(
            SimpleNamespace(
                token="existing-token",
                expires_at=datetime(2099, 1, 1),
            )
        )
        result = await UserService(repository).login(
            username="zhangsan",
            password="example-password",
        )

        assert result["token"] == "existing-token"
        assert repository.updated_token is None
        assert result["userInfo"]["username"] == "zhangsan"

    asyncio.run(verify())


def test_user_login_refreshes_expired_token() -> None:
    """登录时令牌不存在或已过期应创建七日有效的新令牌。"""
    async def verify() -> None:
        repository = FakeLoginRepository(
            SimpleNamespace(
                token="expired-token",
                expires_at=datetime(2020, 1, 1),
            )
        )
        result = await UserService(repository).login(
            username="zhangsan",
            password="example-password",
        )

        assert result["token"] != "expired-token"
        assert repository.updated_token is not None
        assert repository.updated_token.expires_at > datetime.now()

    asyncio.run(verify())


def test_user_login_rejects_invalid_credentials() -> None:
    """登录用户名不存在或密码错误时应拒绝认证。"""
    async def verify() -> None:
        service = UserService(FakeLoginRepository())
        for username, password in (("missing", "example-password"), ("zhangsan", "wrong")):
            try:
                await service.login(username=username, password=password)
            except InvalidCredentialsError:
                continue
            raise AssertionError("错误登录凭据必须被拒绝")

    asyncio.run(verify())


class FakeUserInfoRepository:
    """为用户信息接口测试提供内存令牌和用户数据。"""

    def __init__(self, token: SimpleNamespace | None) -> None:
        """使用可选令牌初始化固定用户。"""
        timestamp = datetime(2026, 8, 11, 9, 0)
        self.token = token
        self.user = SimpleNamespace(
            id=1,
            username="zhangsan",
            created_at=timestamp,
            updated_at=timestamp,
        )

    async def get_token(self, token: str) -> SimpleNamespace | None:
        """按令牌值返回测试令牌。"""
        if self.token is not None and token == self.token.token:
            return self.token
        return None

    async def get_by_id(self, user_id: int) -> SimpleNamespace | None:
        """按用户 ID 返回固定用户。"""
        return self.user if user_id == self.user.id else None


def test_user_info_endpoint_validates_authorization_token() -> None:
    """接口应支持 Bearer 令牌并返回已认证用户的公开信息。"""
    async def fake_service_dependency() -> UserService:
        """为接口测试注入有效令牌。"""
        return UserService(
            FakeUserInfoRepository(
                SimpleNamespace(
                    token="valid-token",
                    user_id=1,
                    expires_at=datetime(2099, 1, 1),
                )
            )
        )

    app.dependency_overrides[get_user_service] = fake_service_dependency
    try:
        response = TestClient(app).get(
            "/api/user/info",
            headers={"Authorization": "Bearer valid-token"},
        )
    finally:
        app.dependency_overrides.pop(get_user_service, None)

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["data"]["username"] == "zhangsan"
    assert "password" not in response.json()["data"]


def test_user_info_endpoint_returns_expired_code_for_expired_token() -> None:
    """接口应在令牌过期时返回 code=402 和登录过期消息。"""
    async def fake_service_dependency() -> UserService:
        """为接口测试注入已过期令牌。"""
        return UserService(
            FakeUserInfoRepository(
                SimpleNamespace(
                    token="expired-token",
                    user_id=1,
                    expires_at=datetime(2020, 1, 1),
                )
            )
        )

    app.dependency_overrides[get_user_service] = fake_service_dependency
    try:
        response = TestClient(app).get(
            "/api/user/info",
            headers={"Authorization": "expired-token"},
        )
    finally:
        app.dependency_overrides.pop(get_user_service, None)

    assert response.status_code == 200
    assert response.json() == {"code": 402, "message": "登录已过期", "data": None}


def test_user_info_endpoint_rejects_missing_or_unknown_token() -> None:
    """接口应在令牌缺失或查询不到时返回认证失败。"""
    async def fake_service_dependency() -> UserService:
        """为接口测试注入空令牌仓储。"""
        return UserService(FakeUserInfoRepository(None))

    app.dependency_overrides[get_user_service] = fake_service_dependency
    try:
        client = TestClient(app)
        missing_response = client.get("/api/user/info")
        unknown_response = client.get(
            "/api/user/info",
            headers={"Authorization": "unknown-token"},
        )
    finally:
        app.dependency_overrides.pop(get_user_service, None)

    for response in (missing_response, unknown_response):
        assert response.status_code == 200
        assert response.json() == {"code": 401, "message": "登录凭证无效", "data": None}
