#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import argcomplete
import asyncio

from controller import (
    MainController,
    ConfigController,
)
from controller.types import (
    SupportedActions,
    SupportedDatabases,
)
from controller.utils.loggers import logger

__app_name__ = 'spider'
__version__ = '0.0.1'


async def main():
    config = ConfigController()

    # TODO(redd4ford): switch to Typer?

    main_parser = argparse.ArgumentParser(description='HTML crawler.')

    main_parser.add_argument(
        '-v', '--version',
        action='version', version=f'{__app_name__} by redd4ford | v{__version__}'
    )

    main_parser.add_argument('--db-user', required=False, default=config.get_db_config('username'))
    main_parser.add_argument('--db-pwd', required=False, default=config.get_db_config('password'))
    main_parser.add_argument('--db-host', required=False, default=config.get_db_config('host'))
    main_parser.add_argument('--db-name', required=False, default=config.get_db_config('name'))
    main_parser.add_argument(
        '--db-type', required=False, choices=SupportedDatabases.all(), default=config.get_db_config('type')
    )
    main_parser.add_argument(
        '--db-update', action='store_true', default=False,
        help=f'update default DB login credentials in `{config.file_name}`'
    )

    subparsers = main_parser.add_subparsers(help='Available commands.')

    get_parser = subparsers.add_parser('get', help='Get URL from DB.')
    get_parser.add_argument('url', help='parent URL address (e.g. https://google.com/')
    get_parser.add_argument(
        '-n',
        type=int, help='number of URLs to get by this parent (default=10)', default=10
    )
    get_parser.set_defaults(func=MainController.get)

    save_parser = subparsers.add_parser('crawl', help='Save URL to the DB.')
    save_parser.add_argument('url', help='URL-address')
    save_parser.add_argument('--depth', type=int, help='depth of scraping (default=1)', default=1)
    save_parser.add_argument(
        '--no-cache', dest='cache', action='store_false',
        help='disable caching of URLs which were scraped during this command run '
             '(leads to DB/file overwrite operations if this link is present in many pages)',
    )
    save_parser.add_argument(
        '--no-logtime', dest='log_time', action='store_false',
        help='do not measure crawler execution time',
    )
    save_parser.add_argument(
        '--silent',
        action='store_true', default=False, help='prevent the logging from crawler'
    )
    save_parser.set_defaults(func=MainController.save)

    db_ops_parser = subparsers.add_parser('cobweb', help='DB operations.')
    db_ops_parser.add_argument('action', choices=SupportedActions.all())
    db_ops_parser.add_argument(
        '--silent',
        action='store_true', default=False, help='prevent the logging from DB/ORM'
    )
    db_ops_parser.set_defaults(func=MainController.db)

    argcomplete.autocomplete(main_parser)   # TODO(redd4ford): finish autocomplete
    args = main_parser.parse_args()

    if config.is_db_config_empty() and any(
        [
            args.db_type is None,
            args.db_user is None,
            args.db_pwd is None,
            args.db_host is None,
            args.db_name is None
        ]
    ):
        logger.warning(
            f'Cannot process your command without database login credentials. '
            f'`{config.file_name}` is empty, and you did not provide full connection details in your args.\n'
            f'The next time you run a command with `--db-type`, `--db-user`, `--db-pwd`, `--db-host`, `--db-name` '
            f'parameters, they will be stored to `{config.file_name}` as default connection values.'
        )
    else:
        if args.db_update or config.is_db_config_empty():
            ConfigController().update(args)

        # TODO(redd4ford): change logging level if --silent is passed
        #  implement a separate loglevel for Crawler and @log_time

        if func := getattr(args, 'func', None):
            await func(args)
        else:
            main_parser.print_usage()


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info('Exiting...')
