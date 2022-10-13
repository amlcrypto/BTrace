"""Database connection factory"""


from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import Session

from config import settings


class DatabaseFactory:

    @staticmethod
    def get_src(name: str, sync: bool = True) -> str:
        return settings.get_database_src(name, sync)

    @classmethod
    def get_async_engine(cls, name: str) -> AsyncEngine:
        return create_async_engine(cls.get_src(name, False))

    @classmethod
    def get_sync_engine(cls, name: str) -> Engine:
        src = cls.get_src(name)
        return create_engine(cls.get_src(name))

    @classmethod
    def get_async_session(cls, name: str) -> AsyncSession:
        return AsyncSession(bind=cls.get_async_engine(name))

    @classmethod
    def get_sync_session(cls, name: str) -> Session:
        return Session(bind=cls.get_sync_engine(name))
