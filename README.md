# Spider
redd4ford | v0.0.1

## How it works

This CLI web crawler stores files to a storage and uses a DB to store the crawled page meta and the file path.

Crawler will print the number of calls and elapsed time in the end of procedure.

The key parameter of `crawl` is `--depth`. Depth lets you specify how many child URLs (`<a>` tags inside the parent URL) you want to crawl. For instance:
* `--depth 0` means "crawl just the parent page"; 
* `--depth 1` means "crawl the parent page and all the links inside the parent page"; 
* `--depth 2` means "crawl the parent page, all the links inside the parent page, and all the links inside those pages";
* and so on.

Spider has a cache to prevent re-loading of the pages that were previously scraped during **this command run**. This means that if parent URL contains the same link as its child (or some children share the same link, etc.), the crawler skips that link.

However, on command re-run, it does not skip the links that were scraped before; instead, it overwrites the files stored and updates the filepath in the DB.

Spider is asynchronous, which ensures that all the pages will eventually be scraped and stored. Donate me a couple of zettabyte hard drives, and I'll scrap the whole Internet with this thing.

Built on abstractions, Spider does not depend on a specific database and/or file writer. This lets us add different implementations of DAO level and (potentially) switch between them.

Currently, it supports HTML scraping and async PostgreSQL with SQLAlchemy.

Uses Python 3.9.

## Installation

### Manually
* Create venv: `python -m venv /path/to/venv`
* Activate venv:
  * Linux/MacOS: source venv/bin/activate
  * Windows: venv\Scripts\activate
* Install requirements: `pip install -r requirements.txt`
* (Opt) create `.env` based on `.env.example` to specify DB credentials.

## Usage

`-h` or `--help` will print you the list of arguments and/or possible actions to perform.

* `python spider.py get [url] -n [int]` - get **n** URLs from the DB where parent URL=**url**
* `python spider.py crawl [url] --depth [int]` - crawl **url** with specified **depth**.
  * `--depth` (default=1) - specify how many child URLs (`<a>` tags) you want to crawl
  * `--silent` (opt) - use this argument to run the command in silent mode, without any logs
* `python spider.py cobweb [action]` - perform DB operations: `drop/create/count`.
  * action=`drop` means "drop the table from the DB and remove all the files stored"
  * action=`create` means "create the table in the DB"
  * action=`count` means "count all the records in the table"
  * `--silent` (opt) - use this argument to run the command in silent mode, without any ORM logs

## TODO

1. Implement a record iterator to display the output for `get`
2. Implement DB operations for Redis, MongoDB, MySQL, Elasticsearch
3. Implement DB switch action in `cobweb`
4. Implement parsing of different types of files (XML, CSS etc.)
5. Implement file type switch parameter in `crawl`
6. Implement propper logging
7. Turn this into a command-line tool with setup options (probably use Typer instead of argparse?)
8. Configure autocomplete
9. Wrap this as a docker-compose

## Why?

First of all, I realized I don't have any projects where BeautifulSoup and asyncio are actually used.

Second of all, I watched a pretty cool anime but there were spiders in it, and I'm afraid of spiders. Google says that you need to face your fears, so I made this.