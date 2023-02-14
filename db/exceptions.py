class DatabaseError(Exception):
    def __init__(self, base_error):
        self.base_error = base_error
        self.message = None
        super().__init__(self.message)


class DatabaseNotFoundError(Exception):
    def __init__(self, db_name=None, db_host=None):
        self.message = (
            f'Database `{db_name}` does not exist in host {db_host}. '
            f'Create the DB first.'
        )
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TableNotFoundError(Exception):
    def __init__(self, table_name=None, db_name=None):
        self.message = (
            f'Table `{table_name}` does not exist in database `{db_name}`. '
            f'Run `spider.py db create` first.'
        )

    def __str__(self):
        return self.message


class TableAlreadyExists(Exception):
    def __init__(self, table_name=None, db_name=None):
        self.message = (
            f'Table `{table_name}` already exists in database `{db_name}`. '
            f'Skipping...'
        )

    def __str__(self):
        return self.message


class CredentialsError(Exception):
    def __init__(self, db_host=None):
        self.message = (
            f'Authentication failed for host {db_host}. '
            f'Double-check your credentials.'
        )

    def __str__(self):
        return self.message
