from controller import (
    Crawler,
    DatabaseOperationsController,
    DelayedKeyboardInterrupt,
)
from db import BaseDatabase


class MainController:
    """
    Handle console commands.
    """

    @classmethod
    async def get(cls, args):
        """
        Select from DB.
        Args:
            :param args: (Namespace) - A set of args entered by the user to perform DB connection,
                provide a URL (:param args.url:) to select by, and optionally limit the number
                of DB entries returned (:param args.n:).
        """
        db_login_args = (
            args.db_user, args.db_pwd, args.db_host, args.db_name
        )
        get_args = (args.url, args.n)

        await DatabaseOperationsController.get(*db_login_args, *get_args)

    @classmethod
    @DatabaseOperationsController.inject_db
    async def save(cls, db: BaseDatabase, args):
        """
        Perform crawling, store data to the DB and to the local files storage.
        Args:
            :param db: (Database) - DB object to handle SELECT operation. This object is
                generated in @DatabaseOperationsController.inject_db and is auto-injected,
                no need to provide it in main().
            :param args: (Namespace) - A set of args entered by the user to perform DB connection,
                provide a URL (:param args.url:) to crawl by, and provide the number of depth
                (:param args.depth:). E.g.:
                    depth=0 means "crawn a main page"
                    depth=1 means "crawl a main page and links inside the main page"
                    depth=2 means "crawl a main page, links inside the main page,
                    and links inside them as well".
                    etc.
        """
        spider = Crawler(db, args.url, args.depth, args.silent)
        with DelayedKeyboardInterrupt():
            await spider.crawl()

    @classmethod
    async def db(cls, args):
        """
        Perform actions on the DB. Currently, supports only "create" and "drop" for the table.
        Args:
            :param args: (Namespace) - A set of args entered by the user to specify the exact
                action (:param args.action:), and perform DB connection.
        """
        action = args.action.lower().strip()
        db_login_args = (
            args.db_user, args.db_pwd, args.db_host, args.db_name
        )

        if action == 'create':
            await DatabaseOperationsController.create_table(*db_login_args)
        elif action == 'drop':
            await DatabaseOperationsController.drop_table(*db_login_args)
        elif action == 'count':
            await DatabaseOperationsController.count_all(*db_login_args)
        else:
            print(f'Action `{action}` is not supported.')
