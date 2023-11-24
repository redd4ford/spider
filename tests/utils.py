import functools
from typing import (
    Any,
    Callable,
)

from pytest_postgresql.janitor import DatabaseJanitor


def with_database_janitor(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Execute test with DatabaseJanitor that removes the test db afterward.
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        db = kwargs.get('test_db')
        with DatabaseJanitor(
            db.user, db.host, db.port, db.dbname, db.version,
            db.password
        ):
            return await func(*args, **kwargs)
    return wrapper
