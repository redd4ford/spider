from controller import (
    Crawler,
    DatabaseOperationsController,
)
from controller.core.context_managers import DelayedKeyboardInterrupt
from controller.core.loggers import logger


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
            args.db_type, args.db_user, args.db_pwd, args.db_host, args.db_name
        )
        get_args = (args.url, args.n)

        await (
            DatabaseOperationsController(*db_login_args)
            .get(*get_args)
        )

    @classmethod
    async def save(cls, args):
        """
        Perform crawling, store data to the DB and to the local file storage.
        Args:
            :param args: (Namespace) - A set of args entered by the user to perform DB connection,
                provide a URL (:param args.url:) to crawl by, and provide the number of depth
                (:param args.depth:). E.g.:
                    depth=0 means "crawl a main page"
                    depth=1 means "crawl a main page and links inside the main page"
                    depth=2 means "crawl a main page, links inside the main page,
                    and links inside them as well".
                    etc.
        """
        db_login_args = (
            args.db_type, args.db_user, args.db_pwd, args.db_host, args.db_name
        )

        crawl_args = (
            args.url, args.depth, args.silent, args.log_time, args.cache
        )

        logger.update_level(args.silent, operation='crawl')

        spider = Crawler(
            DatabaseOperationsController(*db_login_args).db,
            *crawl_args
        )
        with DelayedKeyboardInterrupt():
            await spider.crawl()

    @classmethod
    async def db(cls, args):
        """
        Perform actions on the DB. See class `Actions` which contains all the supported actions.
        Args:
            :param args: (Namespace) - A set of args entered by the user to specify the exact
                action (:param args.action:), and perform DB connection.
        """
        db_login_args = (
            args.db_type, args.db_user, args.db_pwd, args.db_host, args.db_name
        )

        logger.update_level(args.silent, operation='db')

        await (
            DatabaseOperationsController(*db_login_args)
            .run_action(
                action=args.action.lower().strip(),
                silent=args.silent,
            )
        )
