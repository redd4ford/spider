from typing import Any

import aioredis
from sqlalchemy import Table

from controller.utils.loggers import logger
from db import BaseDatabase
from db.schema import urls_table
from db.utils import Singleton
from files_storage import (
    BaseFileWriter,
    HTMLFileWriter,
)


class RedisDatabase(BaseDatabase, metaclass=type(Singleton)):
    """
    Redis DAO, async implementation.
    """

    default_driver: str = 'redis'
    table: Table = urls_table
    file_controller: BaseFileWriter = HTMLFileWriter

    def __init__(self, host: str, login: str, pwd: str, db: str, driver: str = default_driver):
        super().__init__(host, login, pwd, db, driver)
        self.__conn_string = f'{driver}://{login}:{pwd}@{host}'

        self.__redis = None
        self.is_initialized = False

    async def connect(self):
        """
        Initiate database connection.
        """
        self.__redis = await aioredis.create_redis_pool(
            self.__conn_string,
            minsize=5,
            maxsize=10
        )
        await self.__redis.select(1)

    async def disconnect(self):
        """
        Close the pool/session.
        """
        self.__redis.close()
        await self.__redis.wait_closed()

    def engine(self, orm_logging: bool = True):
        return self.__redis

    async def save(self, key: Any, name: str, content: str, parent: str, silent: bool = False):
        """
        Save an entry to the DB.
        """
        if self.__redis.hgetall(key) is not None:
            await self.__redis.hmset(
                key,
                {
                    'title': name,
                    'html': await self.update(key, content, None, silent),
                }
            )
        else:
            await self.__redis.hset(
                key,
                {
                    'title': name,
                    'html': await self.file_controller.write(key, content),
                    'parent': parent,
                }
            )

    async def get(self, parent: str, limit: int = 10) -> dict:
        """
        Select all DB entries where parent link equals :param parent:.
        The number of entries to get can be limited by :param limit:.
        """
        keys = []
        async for key in self.__redis.scan(match=f'*{parent}*'):
            keys.append(key)
            if len(keys) == limit:
                break

        values = await self.__redis.hmget(*keys, 'title')

        data = {}
        for key, value in zip(keys, values):
            data[key] = value
        return data

    async def count_all(self) -> int:
        """
        Count all entries in the DB.
        """
        counter = 0
        async for _ in self.__redis.scan_iter():
            counter += 1
        return counter

    async def update(self, key: Any, content: str, connection, silent: bool) -> str:
        """
        Delete HTML file and store a new one if URL was previously crawled.
        """
        old_html = await self.__redis.hget(key, 'html')

        if old_html:
            self.file_controller.delete(old_html)
            if not silent:
                logger.dbinfo(f'Overwrite file: {old_html}')

        return await self.file_controller.write(key, content)

    async def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        DROP TABLE operation.
        """
        await self.__redis.flushdb()
        await self.disconnect()

    def create_table(self, check_first: bool = False, silent: bool = False):
        """
        CREATE TABLE operation. :param silent: is used to remove logging from an ORM.
        """
        pass
