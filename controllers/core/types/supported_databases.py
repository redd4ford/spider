from controllers.core.types.abstract_types import AbstractEnumType


class SupportedDatabases(AbstractEnumType):
    """
    Supported database implementations for `--db-type` argument.
    """

    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLITE = 'sqlite'
    MONGODB = 'mongodb'
    REDIS = 'redis'
    ELASTICSEARCH = 'elasticsearch'
