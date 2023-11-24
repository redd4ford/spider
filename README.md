# spider
redd4ford | v0.0.1 | Python 3.9

## How it works

This CLI web crawler stores files in storage and uses a DB to store the crawled page meta and the file path.

Crawler will print the number of calls and elapsed time at the end of the procedure.

The key parameter of `crawl` is `--depth`. The depth level lets you specify how many child URLs (`<a>` tags inside the parent URL) you want to crawl. For instance:
* `--depth 0` means "crawl just the parent page"; 
* `--depth 1` means "crawl the parent page and all the links inside the parent page"; 
* `--depth 2` means "crawl the parent page, all the links inside the parent page, and all the links inside those pages";
* and so on.

Spider has a cache to prevent re-loading of the pages that were previously scraped during **this command run**. This means that if the parent URL contains the same link as its child (or some children share the same link, etc.), the crawler skips that link.

However, on command re-run, it does not skip the links that were scraped before; instead, it overwrites the files stored and updates the file path in the DB. You can control that behavior with [command parameters](https://github.com/redd4ford/spider#commands).

Spider is asynchronous, which ensures that all the pages will eventually be scraped and stored. Donate me a couple of zettabyte hard drives, and I'll scrap the whole Internet with this thing.

Built on abstractions, Spider does not depend on a specific database, file storage, and/or file writer. This lets us add different implementations of DAO level and switch between them.

### Features

Currently, you can:
- **Scrap** web pages as HTML;


- **Cache the results** asynchronously to one of the supported databases:

[![PostgreSQL, MySQL, SQLite, Redis, MongoDB, Firebase](https://skillicons.dev/icons?i=postgres,mysql,sqlite,redis,mongodb,firebase&perline=6)](https://skillicons.dev)
- **Store the file contents** locally.

Sounds pretty neat, huh?

## Installation

### Manually
* Create venv: `$ python -m venv /path/to/venv`
* Activate venv:
  * Linux/MacOS: `$ source venv/bin/activate`
  * Windows: `$ venv\Scripts\activate`
* Install requirements: `$ pip install -r requirements.txt`
* (Opt) create `config.ini` based on `config.ini.example` to specify DB credentials.

## Usage

`-h` or `--help` will print you the list of arguments and/or possible actions to perform.

### Config.ini

Spider uses `config.ini` to store your default database and infrastructure credentials. You can create it yourself or add the following arguments to your commands:
* `--db-type` - {postgresql, mysql, sqlite, mongodb, redis, elasticsearch}
* `--db-user` - username
* `--db-pwd` - password
* `--db-host` - host in this format: `IP:PORT`
* `--db-name` - database name

The first time you run a command, these arguments will be stored in a `config.ini` and used as default values whenever you don't provide DB access credentials.

If you wish to overwrite your config defaults (or just any specific value, e.g. database type), add argument `--db-update`.

### Commands

* `$ python cli.py catch [url] -n [int]` - get **n** (default=10) URLs from the DB where parent URL=**url**
* `$ python cli.py crawl [url] --depth [int]` - crawl **url** with specified **depth**.
  * `--depth` (default=1) - specify how many child URLs (`<a>` tags) you want to crawl
  * `--concur` (default=5) - set the concurrency limit to reduce (or increase) stress on your machine and target web server, but keep in mind that crawling may become way slower (or way faster)
  * `--use-proxy` (opt) - use the proxy server specified in your config file when you want to avoid IP blocking or 
  * `--silent` (opt) - use this argument to run the command in silent mode, without any logs from the crawler
  * `--no-cache` (opt) - disable caching of URLs that were already scraped during this run (leads to DB/file overwrite operations if this link is present in many pages)
  * `--no-logtime` (opt) - disable crawler execution time measuring
  * `--no-overwrite` (opt) - disable overwriting the file if it has been scraped before
* `$ python cli.py cobweb [action]` - perform DB operations: `drop/create/count`.
  * action=`create` means "create the table in the DB"
  * action=`drop` means "drop the table from the DB and remove all the files stored"
  * action=`count` means "count all the records in the table"
  * `--silent` (opt) - use this argument to run the command in silent mode, without any ORM logs

## TODO

v0.0.2
- [ ] Implement DB operations for:
  - [x] Redis, 
  - [x] MySQL, 
  - [ ] SQLite,
  - [ ] Firebase,
  - [ ] MongoDB,
  - [ ] Elasticsearch
- [ ] Add tests:
  - [ ] Database layer
    - [ ] PostgreSQL implementation
    - [ ] Redis implementation
    - [ ] MySQL implementation
    - [ ] SQLite implementation
    - [ ] Firebase implementation
    - [ ] MongoDB implementation
    - [ ] Elasticsearch implementation
  - [ ] Crawler


v0.0.3
- [ ] Implement parsing of different file types (XML, CSS, JavaScript, etc.)
- [ ] Add `--file-types (str in the format: html,css,js - choices)` parameter in `crawl` (? or just do `--html`, `--css`, `--js`, `--xml` etc.?)
- [ ] Add tests

v0.0.4
- [ ] Allow saving files to different data volumes (local/AWS S3/Azure Blob/Google Storage/Cloud Storage for Firebase/Google Drive/remote FTP)

v1.0.0
- [ ] Turn this into a command-line tool with setup options
- [ ] Configure autocomplete 
- [ ] Wrap this as a docker-compose

## DONE

- [x] Implement a record iterator to display the output for `get`
- [x] Implement `--no-cache` and `--no-logtime` parameters for decorators
- [x] Implement DB switch - `--db-type` parameter + configparser
- [x] Implement proper logging
- [x] Proxy support
- [x] Add `--concur (int)` parameter in `crawl`
- [x] Add `--no-overwrite (bool)` parameter in `crawl`
- [x] Add tests for the Controller layer

## Why?

First of all, I realized I don't have any projects where BeautifulSoup and asyncio are actually used.

Second of all, I watched a pretty cool anime but there were spiders in it, and I'm afraid of spiders. Google says that you need to face your fears, so I made this.
