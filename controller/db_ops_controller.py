from typing import Type

from yarl import URL

from controller.types import (
    SupportedActions,
    SupportedDatabases,
)
from db import (
    BaseDatabase,
    PostgresDatabase,
)
from db.exceptions import (
    DatabaseNotFoundError,
    TableNotFoundError,
    TableAlreadyExists,
    DatabaseError,
    CredentialsError,
)
from db.utils import RecordSet
from files_storage import (
    BaseFileWriter,
    HTMLFileWriter,
)


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
        print(f'Initialized {self.db_type} `{self.db_name}` to work with table `{self.db_table}`.')

    async def run_action(self, action: str, silent: bool = False):
        if action == SupportedActions.DROP:
            await self.drop_table(silent)
        elif action == SupportedActions.CREATE:
            await self.create_table(silent)
        elif action == SupportedActions.COUNT:
            await self.count_all()
        else:
            print(f'Action `{action}` is not supported.')

    async def get(self, url: str, n: int):
        try:
            parent = URL(url).human_repr()

            fetched = await self.db.get(parent, limit=n)

            if fetched:
                for record in RecordSet(fetched):
                    print(f'{record.url} | {record.title}')
            else:
                print(f'No data found by parent={parent}')

        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableNotFoundError:
            print(TableNotFoundError(self.db_table, self.db_name))
        except CredentialsError:
            print(CredentialsError(self.db_host))

    async def drop_table(self, silent: bool = False):
        try:
            self.db.drop_table(silent=silent)
            DatabaseOperationsController.file_controller.drop_all()
        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableNotFoundError:
            print(TableNotFoundError(self.db_table, self.db_name))
        except DatabaseError as exc:
            print(exc.base_error)
        else:
            print(f'Table was dropped successfully.')

    async def create_table(self, silent: bool = False):
        try:
            self.db.create_table(silent=silent)
        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableAlreadyExists:
            print(TableAlreadyExists(self.db_table, self.db_name))
        except DatabaseError as exc:
            print(exc.base_error)
        else:
            print(f'Table was created successfully.')

    async def count_all(self):
        try:
            counter = await self.db.count_all()
            print(f'Found {counter} entries in the database.')
        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(self.db_name, self.db_host))
        except TableNotFoundError:
            print(TableNotFoundError(self.db_table, self.db_name))
        except CredentialsError:
            print(CredentialsError(self.db_host))

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
        if dao == SupportedDatabases.POSTGRESQL:
            return PostgresDatabase
        else:
            print(
                f'Database type `{dao}` is not supported. Using default from config.'
            )
            return PostgresDatabase
