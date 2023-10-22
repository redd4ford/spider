from typing import Any

import motor.motor_asyncio

from spider.db.core import (
    Borg,
    BaseDatabase,
)
from spider.file_storage import BaseFileWriter
from spider.file_storage import HTMLFileWriter


class MongoDatabase(BaseDatabase, Borg):
    """
    MongoDB DAO, async implementation.
    """

    verbose = 'mongodb'
    default_driver: str = 'mongodb'
    file_controller: BaseFileWriter = HTMLFileWriter

    def __init__(
        self, host: str, login: str, pwd: str, db: str, driver: str = default_driver
    ):
        super().__init__(host, login, pwd, db, driver)
        self.__conn_string = f'{driver}://{login}:{pwd}@{host}'

        self.__db_name = db
        self.__client = None
        self.__mongo = None
        self.is_initialized = False

    async def connect(self):
        """
        Initiate database connection.
        """
        if not self.is_initialized:
            self.__client = (
                motor
                .motor_asyncio
                .AsyncIOMotorClient(self.__conn_string)
            )
            self.__mongo = self.__client.catch(self.__db_name)
            self.table = self.__mongo[MongoDatabase.table.name]
            self.is_initialized = True

    async def disconnect(self):
        """
        Close the pool/session.
        """
        self.__client.close()

    def engine(self, orm_logging: bool = True):
        return self.__client

    async def save(
        self, key: Any, name: str, content: str, parent: str, silent: bool = False,
        overwrite: bool = True,
    ):
        """
        Save an entry to the DB.
        """
        await self.table.insert_one(data)
        # TODO
        pass

    async def get(self, parent: str, limit: int = 10):
        """
        Select all DB entries where parent link equals :param parent:.
        The number of entries to get can be limited by :param limit:.
        """
        query = {'url': f'{parent}'}

        cursor = self.table.find(
            query,
            {"_id": 0, "url": 1, "title": 1, "parent": 0, "html": 0}
        )

        data = []
        async for document in cursor:
            data.append(document)
            if len(data) == limit:
                break
        return data

    async def count_all(self) -> int:
        """
        Count all entries in the DB.
        """
        return self.table.find().count()

    async def update(
        self, key: Any, content: str, connection, silent: bool, overwrite: bool
    ) -> str:
        """
        Delete HTML file and store a new one if URL was previously crawled.
        """
        # TODO
        pass

    async def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        DROP TABLE operation.
        """
        # TODO
        pass

    async def create_table(self, check_first: bool = False, silent: bool = False):
        """
        Tables do not exist in Redis, so this method is empty.
        """
        # TODO
        pass
