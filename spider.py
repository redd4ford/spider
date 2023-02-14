#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse
import argcomplete
import asyncio
import os
from dotenv import load_dotenv

from controller import MainController


__app_name__ = 'spider'
__version__ = '0.0.1'


async def main():
    load_dotenv()

    # TODO(redd4ford): switch to Typer?

    main_parser = argparse.ArgumentParser(description='HTML crawler.')

    main_parser.add_argument(
        '-v', '--version',
        action='version', version=f'{__app_name__} by redd4ford | v{__version__}'
    )

    main_parser.add_argument('--db_user', required=False, default=os.getenv('DB_USER'))
    main_parser.add_argument('--db_pwd', required=False, default=os.getenv('DB_PASSWORD'))
    main_parser.add_argument('--db_host', required=False, default=os.getenv('DB_HOST'))
    main_parser.add_argument('--db_name', required=False, default=os.getenv('DB'))

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
        '--silent',
        action='store_true', default=False, help='prevent the logging from crawler'
    )
    save_parser.set_defaults(func=MainController.save)

    db_ops_parser = subparsers.add_parser('cobweb', help='DB operations.')
    db_ops_parser.add_argument('action', help='drop/create/count')   # TODO(redd4ford): implement DB switch action
    db_ops_parser.add_argument(
        '--silent',
        action='store_true', default=False, help='prevent the logging from DB/ORM'
    )
    db_ops_parser.set_defaults(func=MainController.db)

    argcomplete.autocomplete(main_parser)   # TODO(redd4ford): finish autocomplete
    args = main_parser.parse_args()

    if func := getattr(args, 'func', None):
        await func(args)
    else:
        main_parser.print_usage()


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        # TODO(redd4ford): implement proper logging
        print('Exiting...')
