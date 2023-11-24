from typing import Literal

from yarl import URL

from spider.controllers.core.loggers import logger
from spider.controllers.core.types import SupportedActions
from spider.db.manager import DatabaseManager
from spider.db.core import (
    BaseDatabase,
    RecordSet,
)
from spider.db.exceptions import (
    CredentialsError,
    DatabaseError,
    DatabaseNotFoundError,
    TableAlreadyExists,
    TableNotFoundError,
)
from spider.file_storage import BaseFileWriter
from spider.file_storage import HTMLFileWriter


class DatabaseOperationsController:
    """
    Returns results from the DB operations.
    """

    file_controller: BaseFileWriter = HTMLFileWriter

    def __init__(self, db_type: str, login: str, pwd: str, host: str, db_name: str):
        self._database_manager = DatabaseManager()
        self.db: BaseDatabase = self.__build_database(db_type, login, pwd, host, db_name)
        logger.db_info(
            f'Initialized {self.db.verbose} `{db_name}` to work with '
            f'table `{self.db.table.name}`.'
        )

    async def run_action(
        self, action: Literal["drop", "create", "count"], silent: bool = False
    ):
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
        except (
            CredentialsError, DatabaseNotFoundError, TableNotFoundError, DatabaseError
        ) as exc:
            logger.error(exc)

    async def drop_table(self, silent: bool = False):
        """
        Call DAO to drop the table.
        """
        try:
            await self.db.drop_table(silent=silent)
            DatabaseOperationsController.file_controller.drop_all()
        except (
            CredentialsError, DatabaseNotFoundError, TableNotFoundError, DatabaseError
        ) as exc:
            logger.error(exc)
        else:
            logger.info('Table was dropped successfully.')

    async def create_table(self, silent: bool = False):
        """
        Call DAO to create the table.
        """
        try:
            await self.db.create_table(silent=silent)
        except (
            CredentialsError, DatabaseNotFoundError, TableAlreadyExists, DatabaseError,
        ) as exc:
            logger.error(exc)
        else:
            logger.info('Table was created successfully.')

    async def count_all(self):
        """
        Call DAO to retrieve the total number of entities stored in the DB,
        then log the counter.
        """
        try:
            counter = await self.db.count_all()
        except (
            CredentialsError, DatabaseNotFoundError, TableNotFoundError, DatabaseError
        ) as exc:
            logger.error(exc)
        else:
            logger.info(f'Found {counter} entries in the database.')

    def __build_database(
        self, db_type: str, login: str, pwd: str, host: str, db_name: str
    ) -> BaseDatabase:
        """
        Return object of subclass of BaseDatabase, represents DAO.
        """
        dao = self._database_manager.get_database(database_type=db_type)
        if not dao:
            logger.warning(
                f'Database type `{db_type}` is not supported. Using default from config.'
            )
            dao = self._database_manager.default_database
        return dao(host, login, pwd, db_name)
