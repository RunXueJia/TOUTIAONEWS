"""密码哈希与校验工具。"""

from passlib.context import CryptContext


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希明文密码，返回可持久化的哈希字符串。"""
    return _password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码是否匹配已保存的密码哈希。"""
    return _password_context.verify(password, password_hash)
