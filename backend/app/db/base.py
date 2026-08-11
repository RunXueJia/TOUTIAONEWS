"""应用模型使用的 SQLAlchemy 声明式基类。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy ORM 模型的基础父类。"""
