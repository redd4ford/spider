import abc
from typing import Any

from sqlalchemy import Table

from files_storage import BaseFileWriter


class Singleton(type):
    """
    Singleton as metaclass implementation.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseDatabase(abc.ABC):
    """
    Base Database class to be used as parent for all Database subclasses.
    """

    # TODO(redd4ford): implement DB operations for: Redis, MongoDB, MySQL, Elasticsearch

    file_controller: BaseFileWriter = BaseFileWriter
    table: Table = None

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    async def controller(self):
        pass

    @abc.abstractmethod
    def engine(self, sqlalchemy_logging: bool = True):
        pass

    @abc.abstractmethod
    async def save(self, key: Any, name: str, content: str, parent: str, silent: bool):
        """
        INSERT/CREATE/SAVE operation. Args can be overriden in case it is needed to
        store different types of data.
        """
        pass

    @abc.abstractmethod
    async def get(self, parent: str, limit: int = 10):
        """
        SELECT/GET/RETRIEVE operation. Args can be overriden in case it is needed to store
        different types of data.
        """
        pass

    @abc.abstractmethod
    async def count_all(self):
        """
        COUNT operation.
        """
        pass

    @classmethod
    @abc.abstractmethod
    async def update(cls, key: Any, content: str, connection, silent: bool) -> str:
        """
        ON CONFLICT DO UPDATE operation. This is meant to be used inside save(), so an existing
        connection is passed here.
        """
        pass

    @abc.abstractmethod
    def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        DROP TABLE operation. :param silent: is used to remove logging from an ORM.
        """
        pass

    @abc.abstractmethod
    def create_table(self, check_first: bool = False, silent: bool = False):
        """
        CREATE TABLE operation. :param silent: is used to remove logging from an ORM.
        """
        pass
