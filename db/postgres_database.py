from asyncpgsa import PG
import asyncpg.exceptions
from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import (
    Table,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.sql.expression import (
    select,
    func,
)
from sqlalchemy.dialects.postgresql import insert
import sqlalchemy.exc
from yarl import URL

from db.base_database import (
    BaseDatabase,
    Singleton,
)
from db.exceptions import (
    DatabaseNotFoundError,
    TableNotFoundError,
    TableAlreadyExists,
    DatabaseError,
    CredentialsError,
)
from db.schema import (
    urls_table,
    urls_unique_constraint,
)
from files_storage import (
    BaseFileWriter,
    HTMLFileWriter,
)


class PostgresDatabase(BaseDatabase, metaclass=type(Singleton)):
    """
    PostgreSQL DAO, async implementation.
    """

    file_controller: BaseFileWriter = HTMLFileWriter
    table: Table = urls_table
    unique_constraint: str = urls_unique_constraint

    def __init__(self, host: str, login: str, pwd: str, db: str, driver: str = 'postgresql'):
        super().__init__()
        self.__conn_string = f'{driver}://{login}:{pwd}@{host}/{db}'

        self.__pg = PG()
        self.is_initialized = False

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

    async def controller(self) -> PG:
        """
        Return object that can generate a transaction.
        """
        await self.__init()
        return self.__pg

    def engine(self, silent: bool = False) -> Engine:
        """
        Return sqlalchemy.Engine instance. SQLAlchemy logging can be turned off with
        :param silent:.
        """
        do_logging = not silent
        return create_engine(
            url=self.__conn_string, echo=do_logging
        )

    async def save(self, key: URL, name: str, content: str, parent: str, silent: bool = False):
        """
        Save an entry to the DB.
        """
        try:
            pg = await self.controller()
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
                            'html': await self.update(key, content, conn, silent),
                            'parent': parent
                        }
                    )
                )

                # a hack to avoid asyncpgsa throwing
                # AttributeError: 'Insert' object has no attribute 'parameters'.
                setattr(query, 'parameters', query.compile().params)

                await conn.execute(query)

            if not silent:
                print(f'Save URL: {key}')
        except asyncpg.exceptions.InvalidCatalogNameError:
            raise DatabaseNotFoundError
        except asyncpg.exceptions.UndefinedTableError:
            raise TableNotFoundError
        except asyncpg.exceptions.InvalidPasswordError:
            raise CredentialsError

    async def get(self, parent: str, limit: int = 10):
        """
        Select all DB entries where parent link equals :param parent:.
        The number of entries to get can be limited by :param limit:.
        """
        try:
            pg = await self.controller()
            async with pg.transaction() as conn:
                query = (
                    select([self.table.c.url, self.table.c.title])
                    .where(self.table.c.parent == parent)
                    .limit(limit)
                )

                # TODO(redd4ford): implement Record -> EntriesIterator conversion
                return await conn.fetch(query)
        except asyncpg.exceptions.InvalidCatalogNameError:
            raise DatabaseNotFoundError
        except asyncpg.exceptions.UndefinedTableError:
            raise TableNotFoundError
        except asyncpg.exceptions.InvalidPasswordError:
            raise CredentialsError

    async def update(
        self, url: URL, content: str, connection: PoolConnectionProxy, silent: bool
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
            self.file_controller.delete(old_html)
            if not silent:
                print(f'Override file: {old_html}')

        return await self.file_controller.write(url, content)

    async def count_all(self):
        """
        Count all entries in the DB.
        """
        try:
            pg = await self.controller()
            async with pg.transaction() as conn:
                query = (
                    select([func.count()]).select_from(self.table)
                )

                result = await conn.fetch(query)
                counter = result[0].get('count_1', 0)
                print(f'Found {counter} entries in the DB.')
        except asyncpg.exceptions.InvalidCatalogNameError:
            raise DatabaseNotFoundError
        except asyncpg.exceptions.UndefinedTableError:
            raise TableNotFoundError
        except asyncpg.exceptions.InvalidPasswordError:
            raise CredentialsError
        else:
            await pg.pool.close()

    def drop_table(self, check_first: bool = False, silent: bool = False):
        """
        Drop the table.
        """
        try:
            self.table.drop(self.engine(silent), check_first)
        except sqlalchemy.exc.OperationalError as exc:
            raise DatabaseError(base_error=exc)
        except sqlalchemy.exc.ProgrammingError:
            raise TableNotFoundError

    def create_table(self, check_first: bool = False, silent: bool = False):
        """
        Create the table.
        """
        try:
            self.table.create(self.engine(silent), check_first)
        except sqlalchemy.exc.OperationalError as exc:
            raise DatabaseError(base_error=exc)
        except sqlalchemy.exc.ProgrammingError:
            raise TableAlreadyExists
