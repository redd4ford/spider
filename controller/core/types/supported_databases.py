from controller.core.types.abstract_type import AbstractType


class SupportedDatabases(AbstractType):
    """
    Supported database implementations for `--db-type` argument.
    """

    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLITE = 'sqlite'
    MONGODB = 'mongodb'
    REDIS = 'redis'
    ELASTICSEARCH = 'elasticsearch'
