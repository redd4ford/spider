from typing import (
    Dict,
    List,
    Optional,
)

import aioredis
from yarl import URL

from controllers.core.loggers import logger
from db.core import (
    BaseDatabase,
    Borg,
)
from db.exceptions import (
    CredentialsError,
    DatabaseError,
)
from file_storage.core import BaseFileWriter
from file_storage.implementations import HTMLFileWriter


class RedisDatabase(BaseDatabase, Borg):
    """
    Redis DAO, async implementation.
    """

    verbose = 'redis'
    default_driver: str = 'redis'
    file_controller: BaseFileWriter = HTMLFileWriter

    def __init__(
        self, host: str, login: str, pwd: str, db: str, driver: str = default_driver
    ):
        super().__init__(host, login, pwd, db, driver)
        if login and pwd:
            self.__conn_string = f'{driver}://{login}:{pwd}@{host}/{db}'
        else:
            self.__conn_string = f'{driver}://{host}/{db}'

        self.__db_host = host

        self.__redis: Optional[aioredis.commands.Redis] = None
        self.is_initialized = False

    async def connect(self):
        """
        Initiate database connection.
        """
        try:
            if not self.is_initialized:
                self.__redis: aioredis.commands.Redis = (
                    await aioredis.create_redis_pool(
                        self.__conn_string,
                        minsize=5,
                        maxsize=10
                    )
                )
                self.is_initialized = True
        except AssertionError:
            raise DatabaseError(
                base_error='DB name for a Redis database should be a digit (0-15)'
            )
        except ConnectionRefusedError:
            raise DatabaseError(
                base_error='Connection failed. Check if your Redis instance is up'
            )
        except aioredis.errors.AuthError as exc:
            if "ERR invalid password" in str(exc):
                raise CredentialsError(db_host=self.__db_host)
            else:
                raise DatabaseError(
                    base_error='Authentication failed. Your Redis instance does not have '
                               'a password set'
                )

    async def disconnect(self):
        """
        Close the pool/session.
        """
        if self.is_initialized:
            self.is_initialized = not self.is_initialized
            self.__redis.quit()

    def engine(self, orm_logging: bool = True):
        return self.__redis

    async def save(
        self, key: URL, name: str, content: str, parent: str, silent: bool = False
    ):
        """
        Save an entry to the DB.
        """
        if name is None:
            return

        existing_record = await self.__redis.hgetall(str(key))
        if existing_record is not None:
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

    async def get(self, parent: str, limit: int = 10) -> List[Dict[str, str]]:
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
                keys.extend(key)
            if len(keys) == limit:
                break

        data = []
        if keys:
            values = await self.__redis.hmget(*keys, 'title')
            for key, value in zip(keys, values):
                data.append(
                    {
                        'url': key.decode('utf-8'),
                        'title': value.decode('utf-8') if value else ''
                    }
                )
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
            cur, record_set = await self.__redis.scan(cur, match='*')
            if record_set:
                counter += len(record_set)
        await self.disconnect()
        return counter

    async def update(self, key: URL, content: str, _, silent: bool) -> str:
        """
        Delete HTML file and store a new one if URL was previously crawled.
        """
        old_html = await self.__redis.hmget(str(key), 'html')
        if len(old_html) == 1 and old_html[0]:
            old_html = old_html[0].decode('utf-8')

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
