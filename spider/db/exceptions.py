import sqlalchemy


class DatabaseError(Exception):
    def __init__(self, base_error):
        self.message = self.format_exception(base_error)
        super().__init__(self.message)

    @classmethod
    def format_exception(cls, exc: Exception) -> str:
        if type(exc) is sqlalchemy.exc.OperationalError:
            message = str(exc.orig).replace('\n', '').capitalize()
            if not message.endswith('.') or not message.endswith('?'):
                message += '.'
        else:
            try:
                code, message = eval(str(exc))
            except SyntaxError:
                message = str(exc)
            message = message.replace('\n', '').capitalize()
            if not message.endswith('.') or not message.endswith('?'):
                message += '.'
        return message


class DatabaseNotFoundError(Exception):
    def __init__(self, db_name=None, db_host=None):
        self.message = (
            f'Database `{db_name}` does not exist in host {db_host}. '
            'Create the DB first.'
        )
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TableNotFoundError(Exception):
    def __init__(self, table_name=None, db_name=None):
        self.message = (
            f'Table `{table_name}` does not exist in database `{db_name}`. '
            'Run `cli.py cobweb create` first.'
        )

    def __str__(self):
        return self.message


class TableAlreadyExists(Exception):
    def __init__(self, table_name=None, db_name=None):
        self.message = (
            f'Table `{table_name}` already exists in database `{db_name}`. '
            'Skipping...'
        )

    def __str__(self):
        return self.message


class CredentialsError(Exception):
    def __init__(self, db_host=None):
        self.message = (
            f'Authentication failed for host {db_host}. '
            'Double-check your credentials.'
        )

    def __str__(self):
        return self.message
