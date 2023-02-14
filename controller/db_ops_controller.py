import functools

from yarl import URL

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
from files_storage import (
    BaseFileWriter,
    HTMLFileWriter
)


class DatabaseOperationsController:
    """
    Returns results from the DB operations.
    """

    file_controller: BaseFileWriter = HTMLFileWriter
    # TODO(redd4ford): design a strategy to change DB
    database: BaseDatabase = PostgresDatabase

    @classmethod
    def inject_db(cls, func):
        @functools.wraps(func)
        async def wrapper(*args):
            connection_data = args[1].__dict__
            db = cls.__get_db(
                login=connection_data.get('db_user'),
                pwd=connection_data.get('db_pwd'),
                host=connection_data.get('db_host'),
                db=connection_data.get('db_name')
            )
            await func(cls, db, args[1])
        return wrapper

    @classmethod
    async def get(cls, login, pwd, host, db_name, url, n):
        db = cls.__get_db(login, pwd, host, db_name)
        try:
            parent = URL(url).human_repr()

            fetched = await db.get(parent, limit=n)

            if fetched:
                for record in fetched:
                    url, title = record
                    print(f'{url} | {title}')
            else:
                print(f'No data found by parent={parent}')

        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(db_name, host))
        except TableNotFoundError:
            print(TableNotFoundError(db.table.name, db_name))
        except CredentialsError:
            print(CredentialsError(host))

    @classmethod
    async def drop_table(cls, login, pwd, host, db_name, silent: bool = False) -> None:
        db = cls.__get_db(login, pwd, host, db_name)
        try:
            db.drop_table(silent=silent)
            cls.file_controller.drop_all()
        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(db_name, host))
        except TableNotFoundError:
            print(TableNotFoundError(db.table.name, db_name))
        except DatabaseError as exc:
            print(exc.base_error)
        else:
            print(f'Table was dropped successfully.')

    @classmethod
    async def create_table(cls, login, pwd, host, db_name, silent: bool = False) -> None:
        db = cls.__get_db(login, pwd, host, db_name)
        try:
            db.create_table(silent=silent)
        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(db_name, host))
        except TableAlreadyExists:
            print(TableAlreadyExists(db.table.name, db_name))
        except DatabaseError as exc:
            print(exc.base_error)
        else:
            print(f'Table was created successfully.')

    @classmethod
    async def count_all(cls, login, pwd, host, db_name) -> None:
        db = cls.__get_db(login, pwd, host, db_name)
        try:
            await db.count_all()
        except DatabaseNotFoundError:
            print(DatabaseNotFoundError(db_name, host))
        except TableNotFoundError:
            print(TableNotFoundError(db.table.name, db_name))
        except CredentialsError:
            print(CredentialsError(host))

    @classmethod
    def __get_db(cls, login, pwd, host, db) -> BaseDatabase:
        """
        Return object of subclass of BaseDatabase, represents DAO.
        """
        db = cls.database(
            login=login,
            pwd=pwd,
            host=host,
            db=db,
        )
        return db
