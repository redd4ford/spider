from typing import (
    Dict,
    List,
    Union,
)

from aiomysql.sa import (
    create_engine,
    Engine,
    SAConnection,
)
import MySQLdb
import pymysql.err
import sqlalchemy.exc
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.schema import (
    CreateTable,
    DropTable,
)
from sqlalchemy.sql.expression import select
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
from spider.db.schema import (
    urls_unique_constraint
)
from spider.file_storage import (
    BaseFileWriter,
    HTMLFileWriter,
)


class MySqlDatabase(BaseDatabase, Borg):
    """
    MySQL DAO, async implementation.
    """

    verbose = 'mysql'
    default_driver = 'mysql'
    file_controller: BaseFileWriter = HTMLFileWriter
    unique_constraint: str = urls_unique_constraint

    def __init__(
        self, host: str, login: str, pwd: str, db: str, driver: str = default_driver
    ):
        super().__init__(host, login, pwd, db, driver)
        self.__db_host = host
        self.__login = login
        self.__pwd = pwd
        self.__db_name = db

        self.is_initialized = False
        self.__mysql = None

    async def __init(self, silent: bool):
        """
        Initialize MySQL pool if was not initialized.
        """
        if not self.is_initialized:
            self.__mysql = await self.engine(silent)
            self.is_initialized = True

    async def connect(self, silent: bool = False) -> Engine:
        """
        Return object that can generate a transaction.
        """
        try:
            await self.__init(silent)
            return self.__mysql
        except ConnectionRefusedError as exc:
            raise DatabaseError(base_error=exc)
        except Exception as exc:
            raise DatabaseError(base_error=exc)

    async def disconnect(self):
        """
        Close the pool.
        """
        if self.is_initialized:
            self.is_initialized = not self.is_initialized
            self.__mysql.close()
            await self.__mysql.wait_closed()

    async def engine(self, silent: bool = False) -> Engine:
        """
        Return engine instance. SQLAlchemy logging can be turned off with
        :param silent:.
        """
        do_logging = not silent
        try:
            host, port = self.__db_host.split(':')
            return await create_engine(
                host=host, port=int(port), db=self.__db_name,
                user=self.__login, password=self.__pwd,
                minsize=5, maxsize=100, echo=do_logging
            )
        except (
            pymysql.err.OperationalError, sqlalchemy.exc.OperationalError,
            MySQLdb.OperationalError
        ) as exc:
            self.__throw_operational_error(exc)
        except ModuleNotFoundError as exc:
            raise DatabaseError(
                base_error=f'An error ocurred during {self.verbose} '
                           f'engine initialization: {exc}. Check if you have a Python '
                           f'connector installed that is supported by your OS.'
            )

    async def save(
        self, key: URL, name: str, content: str, parent: str, silent: bool = False,
        overwrite: bool = True
    ):
        """
        Save an entry to the DB.
        """
        engine = await self.connect(silent=True)
        try:
            async with engine.acquire() as conn:
                async with conn.begin() as transaction:
                    query = (
                        insert(self.table)
                        .values(
                            url=str(key),
                            title=name,
                            html=await self.file_controller.write(key, content),
                            parent=parent
                        )
                        .on_duplicate_key_update(
                            title=name,
                            html=await self.update(key, content, conn, silent, overwrite),
                            parent=parent
                        )
                    )

                    await conn.execute(query)
                    await transaction.commit()

            logger.crawl_info(f'Save URL: {key}')
        except Exception as e:
            print(e, type(e))   # TODO: catch more exceptions

    async def get(self, parent: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Select all DB entries where parent link equals :param parent:.
        The number of entries to get can be limited by :param limit:.
        """
        engine = await self.connect(silent=True)
        try:
            async with engine.acquire() as conn:
                query = (
                    select([self.table.c.url, self.table.c.title])
                    .where(self.table.c.parent == parent)
                    .limit(limit)
                )
                result = await conn.execute(query)
        except pymysql.err.ProgrammingError:
            raise TableNotFoundError(self.table.name, self.__db_name)
        except (
            pymysql.err.OperationalError, sqlalchemy.exc.OperationalError,
            MySQLdb.OperationalError
        ) as exc:
            self.__throw_operational_error(exc)
        except Exception as e:
            print(e, type(e))   # TODO: catch more exceptions
        finally:
            await self.disconnect()
        return [dict(record) for record in await result.fetchall()]

    async def update(
        self, url: URL, content: str, connection: SAConnection, silent: bool,
        overwrite: bool
    ) -> str:
        """
        Delete HTML file and store a new one if URL was previously crawled.
        """
        query = (
            select([self.table.c.html])
            .where(self.table.c.url == str(url))
        )

        result = await connection.execute(query)
        old_html = await result.fetchone()

        if old_html:
            html = dict(old_html).get('html')
            if overwrite:
                self.file_controller.delete(html)
                logger.crawl_info(f'Overwrite file: {html}')
            else:
                return html
        return await self.file_controller.write(url, content)

    async def count_all(self) -> int:
        """
        Count all entries in the DB.
        """
        engine = await self.connect()
        try:
            async with engine.acquire() as conn:
                query = self.table.select()
                result = await conn.execute(query)
                result = result.rowcount
        except (
            pymysql.err.OperationalError, sqlalchemy.exc.OperationalError,
            MySQLdb.OperationalError
        ) as exc:
            self.__throw_operational_error(exc)
        except pymysql.err.ProgrammingError:
            raise TableNotFoundError(self.table.name, self.__db_name)
        finally:
            await self.disconnect()
        return result

    async def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        Drop the table.
        """
        engine = await self.connect(silent)
        try:
            async with engine.acquire() as conn:
                await conn.execute(DropTable(self.table, if_exists=check_first))
        except (
            pymysql.err.OperationalError, sqlalchemy.exc.OperationalError,
            MySQLdb.OperationalError
        ) as exc:
            self.__throw_operational_error(exc)
        finally:
            await self.disconnect()

    async def create_table(self, check_first: bool = False, silent: bool = False):
        """
        Create the table.
        """
        engine = await self.connect(silent)
        try:
            if silent:
                import warnings
                warnings.filterwarnings('ignore', module=r"aiomysql")

            async with engine.acquire() as conn:
                await conn.execute(CreateTable(self.table, if_not_exists=check_first))
        except (
            pymysql.err.OperationalError, sqlalchemy.exc.OperationalError,
            MySQLdb.OperationalError
        ) as exc:
            self.__throw_operational_error(exc)
        finally:
            await self.disconnect()

    def __throw_operational_error(
        self, exc: Union[
            pymysql.err.OperationalError, sqlalchemy.exc.OperationalError,
            MySQLdb.OperationalError
        ]
    ):
        message = str(exc).lower()
        if "already exists" in message:
            raise TableAlreadyExists(self.table.name, self.__db_name)
        elif "unknown table" in message:
            raise TableNotFoundError(self.table.name, self.__db_name)
        elif "unknown database" in message:
            raise DatabaseNotFoundError(self.__db_name, self.__db_host)
        elif "access denied" in message:
            raise CredentialsError(self.__db_host)
        elif "can't connect" in message:
            raise DatabaseError(
                base_error=DatabaseError.format_exception(exc) +
                ' If your server is running and you can access it, it is likely that '
                f'database `{self.__db_name}` does not exist.')
        else:
            raise DatabaseError(base_error=exc)
