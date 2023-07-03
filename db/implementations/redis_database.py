from typing import Any

import aioredis
from sqlalchemy import Table

from controller.core.loggers import logger
from db.schema import urls_table
from db.core import (
    Singleton,
    BaseDatabase,
)
from file_storage.core import BaseFileWriter
from file_storage.implementations import HTMLFileWriter


class RedisDatabase(BaseDatabase, metaclass=type(Singleton)):
    """
    Redis DAO, async implementation.
    """

    default_driver: str = 'redis'
    table: Table = urls_table
    file_controller: BaseFileWriter = HTMLFileWriter

    def __init__(self, host: str, login: str, pwd: str, db: str, driver: str = default_driver):
        super().__init__(host, login, pwd, db, driver)
        if not db.isdigit():
            logger.error('DB name for a redis database should be a digit (0-15)')
        self.__conn_string = f'{driver}://{host}/{db}'

        self.__redis = None
        self.is_initialized = False

    async def connect(self):
        """
        Initiate database connection.
        """
        if not self.is_initialized:
            self.__redis: aioredis.commands.Redis = (
                await aioredis.create_redis_pool(
                    self.__conn_string,
                    minsize=5,
                    maxsize=10
                )
            )
            self.is_initialized = True

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
        if name is None:
            return

        await self.connect()
        if await self.__redis.hgetall(str(key)) is not None:
            html = await self.update(key, content, None, silent)
            await self.__redis.hmset_dict(
                str(key),
                {
                    'title': name,
                    'html': html,
                }
            )
        else:
            html = await self.file_controller.write(key, content)
            await self.__redis.hmset_dict(
                str(key),
                {
                    'title': name,
                    'html': html,
                    'parent': parent,
                }
            )

    async def get(self, parent: str, limit: int = 10) -> dict:
        """
        Select all DB entries where parent link equals :param parent:.
        The number of entries to get can be limited by :param limit:.
        """
        await self.connect()
        keys = []
        cur = b'0'
        while cur:
            cur, key = await self.__redis.scan(cur, match=f'*{parent}*')
            if key:
                keys.append(key)
            if len(keys) == limit:
                break

        data = {}
        if keys:
            values = await self.__redis.hmget(*keys, 'title')
            for key, value in zip(keys, values):
                data[key] = value.decode('utf-8')
        await self.disconnect()
        return data

    async def count_all(self) -> int:
        """
        Count all entries in the DB.
        """
        await self.connect()
        cur = b'0'
        counter = 0
        while cur:
            cur, record = await self.__redis.scan(cur, match='*')
            if record:
                counter += 1
        await self.disconnect()
        return counter

    async def update(self, key: Any, content: str, connection, silent: bool) -> str:
        """
        Delete HTML file and store a new one if URL was previously crawled.
        """
        await self.connect()
        old_html = await self.__redis.hmget(str(key), 'html')
        if len(old_html) == 1 and old_html[0] is not None:
            old_html = old_html[0].decode('utf-8')
        else:
            old_html = None

        if old_html is not None:
            self.file_controller.delete(old_html)
            logger.crawl_info(f'Overwrite file: {old_html}')

        file_path = await self.file_controller.write(key, content)
        return file_path

    async def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        DROP TABLE operation.
        """
        await self.connect()
        await self.__redis.flushdb()
        await self.disconnect()

    def create_table(self, check_first: bool = False, silent: bool = False):
        """
        Tables do not exist in Redis, so this method is empty.
        """
        pass
