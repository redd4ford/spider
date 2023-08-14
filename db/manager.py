from typing import (
    Dict,
    List,
    Optional,
    Type,
)

from db.core import (
    BaseDatabase,
    Borg,
)
from db.implementations import (
    MongoDatabase,
    PostgresDatabase,
    RedisDatabase,
)


class DatabaseManager(Borg):
    """
    Holds all supported database implementations for `--db-type` argument.
    """

    def __init__(self, databases: Dict[str, Type[BaseDatabase]] = None) -> None:
        super().__init__()
        if databases:
            self._databases = databases
        else:
            # initiate the first instance with default state
            if not hasattr(self, "_databases"):
                self._databases = {}

    def _inject(self, database: Type[BaseDatabase]):
        """
        Add database of type :param database: to the list of supported databases.
        """
        self._databases[database.verbose] = database

    @property
    def choices(self) -> List[str]:
        """
        Return the list of supported database types.
        """
        return list(self._databases.keys())

    @property
    def default_database(self) -> Type[BaseDatabase]:
        """
        A default DAO implementation to use if the user passed a database type that is
        not supported yet.
        """
        return PostgresDatabase

    def get_database(self, database_type: str) -> Optional[Type[BaseDatabase]]:
        """
        Get DAO implementation by :param database_type:. Returns None if there is no
        injected implementations for the specified type.
        """
        return self._databases.get(database_type, None)

    def run(self):
        """
        Perform injection of DAO implementations.
        """
        self._inject(database=PostgresDatabase)
        self._inject(database=RedisDatabase)
