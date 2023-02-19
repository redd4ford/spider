from controller.types.abstract_type import AbstractType


class SupportedDatabases(AbstractType):
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLITE = 'sqlite'
    MONGODB = 'mongodb'
    REDIS = 'redis'
    ELASTICSEARCH = 'elasticsearch'
