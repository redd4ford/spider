from typing import Type

from yarl import URL

from controller.core.loggers import logger
from controller.core.types import (
    SupportedActions,
    SupportedDatabases,
)
from db.core import (
    BaseDatabase,
    RecordSet,
)
from db.implementations import (
    PostgresDatabase,
    RedisDatabase,
)
from db.exceptions import (
    DatabaseNotFoundError,
    TableNotFoundError,
    TableAlreadyExists,
    DatabaseError,
    CredentialsError,
)
from file_storage.core import BaseFileWriter
from file_storage.implementations import HTMLFileWriter


class DatabaseOperationsController:
    """
    Returns results from the DB operations.
    """

    file_controller: BaseFileWriter = HTMLFileWriter

    def __init__(self, db_type: str, login: str, pwd: str, host: str, db_name: str):
        self.__dao_impl: Type[BaseDatabase] = self.__choose_dao_implementation(db_type)
        self.db = self.__get_dao(login, pwd, host, db_name)
        self.db_host = host
        self.db_name = db_name
        self.db_type = db_type
        self.db_table = self.db.table.name
        logger.db_info(f'Initialized {self.db_type} `{self.db_name}` to work with table `{self.db_table}`.')

    async def run_action(self, action: str, silent: bool = False):
        """
        Map :param action: to a specific method.
        """
        if action == SupportedActions.DROP:
            await self.drop_table(silent)
        elif action == SupportedActions.CREATE:
            await self.create_table(silent)
        elif action == SupportedActions.COUNT:
            await self.count_all()
        else:
            logger.error(f'Action `{action}` is not supported.')

    async def get(self, url: str, limit: int):
        """
        Call DAO to get all URLs from the DB by parent :param url:, then log them.
        The number of values is limited by :param limit:.
        """
        try:
            parent = URL(url).human_repr()

            fetched = await self.db.get(parent, limit)

            if fetched:
                for counter, record in enumerate(RecordSet(fetched), start=1):
                    logger.info(f'#{counter} {record.url} | {record.title}')
            else:
                logger.info(f'No data found by parent={parent}')

        except DatabaseNotFoundError:
            logger.error(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableNotFoundError:
            logger.error(TableNotFoundError(self.db_table, self.db_name))
        except CredentialsError:
            logger.error(CredentialsError(self.db_host))

    async def drop_table(self, silent: bool = False):
        """
        Call DAO to drop the table.
        """
        try:
            self.db.drop_table(silent=silent)
            DatabaseOperationsController.file_controller.drop_all()
        except DatabaseNotFoundError:
            logger.error(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableNotFoundError:
            logger.error(TableNotFoundError(self.db_table, self.db_name))
        except DatabaseError as exc:
            logger.error(exc.base_error)
        else:
            logger.info(f'Table was dropped successfully.')

    async def create_table(self, silent: bool = False):
        """
        Call DAO to create the table.
        """
        try:
            self.db.create_table(silent=silent)
        except DatabaseNotFoundError:
            logger.error(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableAlreadyExists:
            logger.error(TableAlreadyExists(self.db_table, self.db_name))
        except DatabaseError as exc:
            logger.error(exc.base_error)
        else:
            logger.info(f'Table was created successfully.')

    async def count_all(self):
        """
        Call DAO to retrieve the total number of entities stored in the DB,
        then log the counter.
        """
        try:
            counter = await self.db.count_all()
        except DatabaseNotFoundError:
            logger.error(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableNotFoundError:
            logger.error(TableNotFoundError(self.db_table, self.db_name))
        except CredentialsError:
            logger.error(CredentialsError(self.db_host))
        else:
            logger.info(f'Found {counter} entries in the database.')

    def __get_dao(self, login: str, pwd: str, host: str, db: str) -> BaseDatabase:
        """
        Return object of subclass of BaseDatabase, represents DAO.
        """
        db = self.__dao_impl(
            login=login,
            pwd=pwd,
            host=host,
            db=db,
        )
        return db

    @classmethod
    def __choose_dao_implementation(cls, dao: str) -> Type[BaseDatabase]:
        """
        Return type of subclass of BaseDatabase.
        """
        if dao == SupportedDatabases.POSTGRESQL:
            return PostgresDatabase
        elif dao == SupportedDatabases.REDIS:
            return RedisDatabase
        else:
            logger.warning(
                f'Database type `{dao}` is not supported. Using default from config.'
            )
            return PostgresDatabase
