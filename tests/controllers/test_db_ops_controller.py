import pytest
from pytest_postgresql import factories
from yarl import URL

from tests.utils import with_database_janitor

try:
    from spider.controllers import DatabaseOperationsController
except ImportError:
    import sys
    sys.path.append('../spider')
    from spider.controllers import DatabaseOperationsController

from spider.db.implementations import PostgresDatabase


test_db = factories.postgresql_proc(port=None, dbname="test_db")


class TestDatabaseOperationsController:
    @pytest.mark.asyncio
    @with_database_janitor
    async def test_run_action(self, test_db, caplog):
        controller = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:{test_db.port}",
            login=test_db.user, pwd=test_db.password,
            db_name=test_db.dbname
        )
        assert (
            f'Initialized postgresql `{test_db.dbname}` to work with table' in caplog.text
        )
        assert type(controller.db) is PostgresDatabase
        await controller.run_action(action='create')
        assert 'Table was created successfully.' in caplog.text
        await controller.run_action(action='count')
        assert 'Found 0 entries in the database.' in caplog.text
        await controller.run_action(action='drop')
        assert 'Table was dropped successfully.' in caplog.text
        # noinspection PyTypeChecker
        await controller.run_action(action='undefined')
        assert 'Action `undefined` is not supported.' in caplog.text

    @pytest.mark.asyncio
    @with_database_janitor
    async def test_initialize_database_with_wrong_credentials(self, test_db, caplog):
        # wrong db host
        controller = DatabaseOperationsController(
            db_type='postgresql', host=f"wronghost:{test_db.port}",
            login=test_db.user, pwd=test_db.password,
            db_name=test_db.dbname
        )
        await controller.run_action(action='create')
        assert 'Could not translate host name "wronghost"' in caplog.text
        await controller.run_action(action='count')
        assert 'Could not translate host name "wronghost"' in caplog.text
        await controller.run_action(action='drop')
        assert 'Could not translate host name "wronghost"' in caplog.text

        # wrong db port
        controller = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:1234",
            login=test_db.user, pwd=test_db.password,
            db_name=test_db.dbname
        )
        await controller.run_action(action='create')
        assert f'connection refused' in caplog.text
        await controller.run_action(action='count')
        assert f'connection refused' in caplog.text
        await controller.run_action(action='drop')
        assert f'connection refused' in caplog.text

        # wrong db credentials
        controller = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:{test_db.port}",
            login='wronguser', pwd=test_db.password,
            db_name=test_db.dbname
        )
        await controller.run_action(action='create')
        assert 'role "wronguser" does not exist' in caplog.text
        await controller.run_action(action='count')
        assert 'role "wronguser" does not exist' in caplog.text
        await controller.run_action(action='drop')
        assert 'role "wronguser" does not exist' in caplog.text

        # wrong db name
        controller = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:{test_db.port}",
            login=test_db.user, pwd=test_db.password,
            db_name='wrongdb'
        )
        await controller.run_action(action='create')
        assert 'database "wrongdb" does not exist' in caplog.text
        await controller.run_action(action='count')
        assert 'database "wrongdb" does not exist' in caplog.text
        await controller.run_action(action='drop')
        assert 'database "wrongdb" does not exist' in caplog.text

    @pytest.mark.asyncio
    @with_database_janitor
    async def test_try_to_create_nonexisting_db_type(self, test_db, caplog):
        controller = DatabaseOperationsController(
            db_type='my_awesome_db', host=f"{test_db.host}:{test_db.port}",
            login=test_db.user, pwd=test_db.password,
            db_name=test_db.dbname
        )
        assert (
            'Database type `my_awesome_db` is not supported. Using default from config.'
            in caplog.text
        )
        assert (
            f'Initialized postgresql `{test_db.dbname}` to work with table' in caplog.text
        )
        assert type(controller.db) is PostgresDatabase

    @pytest.mark.asyncio
    @with_database_janitor
    async def test_get_data(self, test_db, caplog):
        controller1 = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:{test_db.port}",
            login=test_db.user, pwd=test_db.password,
            db_name=test_db.dbname
        )
        assert (
            f'Initialized postgresql `{test_db.dbname}` to work with table' in caplog.text
        )
        assert type(controller1.db) is PostgresDatabase
        await controller1.run_action(action='create')
        controller2 = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:{test_db.port}",
            login='wronguser', pwd=test_db.password,
            db_name=test_db.dbname
        )
        await controller2.get(url='https://example.com/', limit=5)
        assert 'Authentication failed' in caplog.text
        controller3 = DatabaseOperationsController(
            db_type='postgresql', host=f"{test_db.host}:{test_db.port}",
            login=test_db.user, pwd=test_db.password,
            db_name=test_db.dbname
        )
        await controller3.get(url='https://example.com/', limit=5)
        assert 'No data found by parent=https://example.com/' in caplog.text
        # force-save something
        await controller3.db.save(
            key=URL('https://example.com'), name='Example Domain', content='test',
            parent='https://example.com/', silent=False, overwrite=False
        )
        await controller3.get(url='https://example.com/', limit=5)
        assert '#1 https://example.com | Example Domain' in caplog.text
