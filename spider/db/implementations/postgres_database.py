import socket
from typing import (
    Dict,
    List,
)

from asyncpgsa import PG
import asyncpg.exceptions
from asyncpg.pool import PoolConnectionProxy
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine, create_engine
import sqlalchemy.exc
from sqlalchemy.sql.expression import (
    func,
    select,
)
from yarl import URL

from spider.controllers.core.loggers import logger
from spider.db.core import (
    BaseDatabase,
    Borg,
)
from spider.db.exceptions import (
    CredentialsError,
    DatabaseError,
    DatabaseNotFoundError,
    TableAlreadyExists,
    TableNotFoundError,
)
from spider.db.schema import urls_unique_constraint
from spider.file_storage import BaseFileWriter
from spider.file_storage import HTMLFileWriter


class PostgresDatabase(BaseDatabase, Borg):
    """
    PostgreSQL DAO, async implementation.
    """

    verbose = 'postgresql'
    default_driver: str = 'postgresql'
    file_controller: BaseFileWriter = HTMLFileWriter
    unique_constraint: str = urls_unique_constraint

    def __init__(
        self, host: str, login: str, pwd: str, db: str, driver: str = default_driver
    ):
        super().__init__(host, login, pwd, db, driver)
        self.__conn_string = f'{driver}://{login}:{pwd}@{host}/{db}'
        self.__db_host = host
        self.__db_name = db

        self.is_initialized = False
        self.__pg = PG()

    async def __init(self):
        """
        Initialize PG pool if was not initialized.
        """
        if not self.is_initialized:
            await self.__pg.init(
                self.__conn_string,
                min_size=5,
                max_size=100
            )
            self.is_initialized = True

    async def connect(self) -> PG:
        """
        Return object that can generate a transaction.
        """
        try:
            await self.__init()
            return self.__pg
        except (
            asyncpg.exceptions.InvalidPasswordError,
            asyncpg.exceptions.InvalidAuthorizationSpecificationError,
        ):
            raise CredentialsError(self.__db_host)
        except (socket.gaierror, ConnectionRefusedError) as exc:
            raise DatabaseError(base_error=exc)
        except asyncpg.exceptions.InvalidCatalogNameError:
            raise DatabaseNotFoundError(self.__db_name, self.__db_host)

    async def disconnect(self):
        """
        Close the pool.
        """
        if self.is_initialized:
            self.is_initialized = not self.is_initialized
            await self.__pg.pool.close()

    def engine(self, silent: bool = False) -> Engine:
        """
        Return sqlalchemy.Engine instance. SQLAlchemy logging can be turned off with
        :param silent:.
        """
        do_logging = not silent
        return create_engine(
            url=self.__conn_string, echo=do_logging
        )

    async def save(
        self, key: URL, name: str, content: str, parent: str, silent: bool = False,
        overwrite: bool = True
    ):
        """
        Save an entry to the DB.
        """
        try:
            pg = await self.connect()
            async with pg.transaction() as conn:
                query = (
                    insert(self.table)
                    .values(
                        url=str(key),
                        title=name,
                        html=await self.file_controller.write(key, content),
                        parent=parent
                    )
                    .on_conflict_do_update(
                        constraint=self.unique_constraint,
                        set_={
                            'title': name,
                            'html': await self.update(
                                key, content, conn, silent, overwrite
                            ),
                            'parent': parent
                        }
                    )
                )

                # a hack to avoid asyncpgsa throwing
                # AttributeError: 'Insert' object has no attribute 'parameters'.
                setattr(query, 'parameters', query.compile().params)

                await conn.execute(query)

            logger.crawl_info(f'Save URL: {key}')
        except asyncpg.exceptions.UndefinedTableError:
            raise TableNotFoundError(self.table.name, self.__db_name)

    async def get(self, parent: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Select all DB entries where parent link equals :param parent:.
        The number of entries to get can be limited by :param limit:.
        """
        try:
            pg = await self.connect()
            async with pg.transaction() as conn:
                query = (
                    select([self.table.c.url, self.table.c.title])
                    .where(self.table.c.parent == parent)
                    .limit(limit)
                )
                records = await conn.fetch(query)
            return [dict(record) for record in records]
        except asyncpg.exceptions.UndefinedTableError:
            raise TableNotFoundError(self.table.name, self.__db_name)

    async def update(
        self, url: URL, content: str, connection: PoolConnectionProxy, silent: bool,
        overwrite: bool
    ) -> str:
        """
        Delete HTML file and store a new one if URL was previously crawled.
        """
        query = (
            select([self.table.c.html])
            .where(self.table.c.url == str(url))
        )

        old_html = await connection.fetchval(query)

        if old_html:
            if overwrite:
                self.file_controller.delete(old_html)
                logger.crawl_info(f'Overwrite file: {old_html}')
            else:
                return old_html
        return await self.file_controller.write(url, content)

    async def count_all(self) -> int:
        """
        Count all entries in the DB.
        """
        pg = await self.connect()
        try:
            async with pg.transaction() as conn:
                query = (
                    select([func.count()]).select_from(self.table)
                )

                result = await conn.fetch(query)
        except asyncpg.exceptions.UndefinedTableError:
            raise TableNotFoundError(self.table.name, self.__db_name)
        else:
            await pg.pool.close()
        return result[0].get('count_1', 0)

    async def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        Drop the table.
        """
        try:
            self.table.drop(self.engine(silent), check_first)
        except sqlalchemy.exc.OperationalError as exc:
            raise DatabaseError(base_error=exc)
        except sqlalchemy.exc.ProgrammingError:
            raise TableNotFoundError(self.table.name, self.__db_name)

    async def create_table(self, check_first: bool = False, silent: bool = False):
        """
        Create the table.
        """
        try:
            self.table.create(self.engine(silent), check_first)
        except sqlalchemy.exc.OperationalError as exc:
            raise DatabaseError(base_error=exc)
        except sqlalchemy.exc.ProgrammingError:
            raise TableAlreadyExists(self.table.name, self.__db_name)
