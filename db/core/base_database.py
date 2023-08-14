import abc
from typing import Any

from sqlalchemy import Table

from file_storage.core import BaseFileWriter


class BaseDatabase(abc.ABC):
    """
    Base Database class to be used as parent for all Database subclasses.
    """

    verbose = 'OVERRIDE_THIS'
    file_controller: BaseFileWriter = BaseFileWriter
    table: Table = None

    def __init__(self, _host: str, _login: str, _pwd: str, _db: str, _driver: str = ''):
        super().__init__()

    @abc.abstractmethod
    async def connect(self):
        """
        Initiate database connection.
        """
        pass

    @abc.abstractmethod
    async def disconnect(self):
        """
        Close the pool/session.
        """
        pass

    @abc.abstractmethod
    def engine(self, orm_logging: bool = True):
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
        ON CONFLICT DO UPDATE operation. This is meant to be used inside save(), so
        an existing :param connection: should be passed.
        """
        pass

    @abc.abstractmethod
    async def drop_table(self, check_first: bool = False, silent: bool = False):
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
