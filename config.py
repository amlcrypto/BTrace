"""Config module"""
from pathlib import Path
from typing import Dict

from pydantic import BaseModel

from exceptions import DatabaseConfigError


class DatabaseConfig(BaseModel):
    """Database connection config"""
    dialect: str
    sync_driver: str
    async_driver: str
    user: str
    password: str
    host: str
    port: int
    name: str

    def get_src(self, sync: bool = True) -> str:
        """
        Returns database connection source string
        :param sync: bool - kind of connection (sync or async)
        :return: str
        """
        return '{}+{}://{}:{}@{}:{}/{}'.format(
            self.dialect,
            self.sync_driver if sync else self.async_driver,
            self.user,
            self.password,
            self.host,
            self.port,
            self.name
        )


class Config(BaseModel):
    """Config class. Contains all necessary settings values"""
    TOKEN: str
    databases: Dict[str, DatabaseConfig]
    kafka: str

    def get_database_src(self, name: str, sync: bool = True) -> str:
        """Returns src for specified database"""
        db = self.databases.get(name)
        if not db:
            raise DatabaseConfigError(f"Database {name} config data not exist")
        return db.get_src(sync)

PATH = Path(__file__).resolve().parent
with open(f"{PATH}/config.json", 'r', encoding='utf-8') as f:
    settings = Config.parse_raw(f.read())
