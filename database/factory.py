"""Database connection factory"""


from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import Session

from config import settings


class DatabaseFactory:
    """Connection factory"""
    @staticmethod
    def get_src(name: str, sync: bool = True) -> str:
        """
        Returns database connection src
        :param name: database name
        :type name: str
        :param sync: sync or async
        :type sync: bool
        :return: database connection src
        :rtype: str
        """
        return settings.get_database_src(name, sync)

    @classmethod
    def get_async_engine(cls, name: str) -> AsyncEngine:
        """Create and return database connection async engine"""
        return create_async_engine(cls.get_src(name, False))

    @classmethod
    def get_sync_engine(cls, name: str) -> Engine:
        """Create and return database connection sync engine"""
        return create_engine(cls.get_src(name))

    @classmethod
    def get_async_session(cls, name: str) -> AsyncSession:
        """Create and return database connection async session"""
        return AsyncSession(bind=cls.get_async_engine(name))

    @classmethod
    def get_sync_session(cls, name: str) -> Session:
        """Create and return database connection sync session"""
        return Session(bind=cls.get_sync_engine(name))
