from typing import (
    List,
    Optional,
    Type,
)

from spider.db.core import (
    BaseDatabase,
    Borg,
    DatabaseImplementationInjector,
)
from spider.db.implementations import PostgresDatabase


class DatabaseManager(Borg):
    """
    Holds all supported database implementations for `--db-type` argument, as well as
    all the database-related configurations and constants.
    """

    def __init__(self) -> None:
        super().__init__()
        self._databases = DatabaseImplementationInjector.get_registry().copy()

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
