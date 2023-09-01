from argparse import Namespace

from controllers import DatabaseOperationsController
from controllers.core.context_managers import DelayedKeyboardInterrupt
from controllers.core.loggers import logger
from crawler import Crawler
from crawler.exceptions import IncorrectProxyFormatError


class AppController:
    """
    Handle console commands.
    """

    @classmethod
    async def catch(cls, args: Namespace):
        """
        Select from DB.
        Args:
            :param args: (Namespace) - A set of args entered by the user to perform DB
                connection, provide a URL (:param args.url:) to select by, and optionally
                limit the number of DB entries returned (:param args.n:).
        """
        db_login_args = (
            args.db_type.lower().strip(), args.db_user, args.db_pwd, args.db_host,
            args.db_name
        )
        get_args = (args.url, args.n)

        await (
            DatabaseOperationsController(*db_login_args)
            .get(*get_args)
        )

    @classmethod
    async def save(cls, args: Namespace):
        """
        Perform crawling, store data to the DB and to the local file storage.
        Args:
            :param args: (Namespace) - A set of args entered by the user to perform DB
                connection, provide a URL (:param args.url:) to crawl by, and provide
                the level of depth (:param args.depth:). E.g.:
                    depth=0 means "crawl the page by URL (parent page)",
                    depth=1 means "crawl the parent page and all its nested links",
                    depth=2 means "crawl the parent page, all its nested links,
                    and all the links inside them as well".
                    etc.
        """
        db_login_args = (
            args.db_type.lower().strip(), args.db_user, args.db_pwd, args.db_host,
            args.db_name
        )

        crawl_args = (
            args.url, args.depth, args.silent, args.log_time, args.cache, args.proxy
        )

        logger.update_level(args.silent, operation='crawl')

        try:
            spider = Crawler(
                DatabaseOperationsController(*db_login_args).db, *crawl_args
            )
        except IncorrectProxyFormatError as exc:
            logger.error(exc)
        else:
            with DelayedKeyboardInterrupt():
                await spider.crawl()

    @classmethod
    async def db(cls, args: Namespace):
        """
        Perform actions on the DB. See class `Actions` which contains all the supported
        actions.
        Args:
            :param args: (Namespace) - A set of args entered by the user to specify
                the exact action (:param args.action:), and perform DB connection.
        """
        db_login_args = (
            args.db_type.lower().strip(), args.db_user, args.db_pwd, args.db_host,
            args.db_name
        )

        logger.update_level(args.silent, operation='db')

        await (
            DatabaseOperationsController(*db_login_args)
            .run_action(
                action=args.action.lower().strip(),
                silent=args.silent,
            )
        )
