import asyncio
from typing import (
    Tuple,
    Optional,
)

import httpx
import time
import functools

from bs4 import BeautifulSoup
from yarl import URL

from db import BaseDatabase


def log_time(func):
    """
    Measure the elapsed time of a function/method.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        await func(*args, **kwargs)
        finish_time = time.perf_counter()
        print(f'Elapsed time: {finish_time - start_time}')
    return wrapper


class Crawler:
    """
    Performs crawling of a url with specified depth.
    """

    def __init__(self, database: BaseDatabase, start_url: str, depth: int, silent: bool = False):
        self.client = httpx.AsyncClient()
        self.url = URL(start_url)
        self.db = database
        self.depth = depth
        self.silent = silent

    @classmethod
    def use_cache(cls, do: bool = True, silent: bool = False):
        """
        Skip already crawled URLs to prevent DB override operations.
        """

        cache = set()

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(url, *args):
                if do:
                    if url not in cache:
                        cache.add(url)
                        await func(url, *args)
                    else:
                        if not silent:
                            print(f'Found {url} in cache. Skipping...')
                else:
                    await func(url, *args)
            return wrapper
        return decorator

    @log_time
    async def crawl(self):
        calls = 0

        @self.use_cache(do=True, silent=self.silent)
        async def load(url: URL, level: int):
            nonlocal calls
            calls += 1
            try:
                title, html_body, soup = await self.__load_and_parse(url)
            except TypeError:
                if not self.silent:
                    print(f'Cannot download URL: {url}.')
                return

            asyncio.ensure_future(
                self.db.save(
                    url, title, html_body, parent=self.url.human_repr(), silent=self.silent
                ),
                loop=asyncio.get_running_loop()
            )

            if level >= self.depth:
                return

            refs = self.__generate_refs(soup.findAll('a'))
            todos = [load(ref, level + 1) for ref in refs]
            await asyncio.gather(*todos)

        try:
            # trying to connect to db
            await self.db.controller()
            self.db.create_table(check_first=True, silent=True)
        except Exception as exc:
            print(f'Database error: {exc}')
            return

        try:
            await load(self.url, 0)
        finally:
            await self.client.aclose()
            controller = await self.db.controller()
            await controller.pool.close()
            print('Done.')
            print(f'Calls: {calls}')

    async def __load_and_parse(
        self, url: URL
    ) -> Optional[Tuple[Optional[str], Optional[str], BeautifulSoup]]:
        try:
            res = await self.client.get(str(url))
        except httpx.HTTPError as exc:
            if not self.silent:
                print(f'HTTP Exception for {exc.request.url}')
            return
        except ValueError:
            return

        # noinspection PyTypeChecker
        soup = BeautifulSoup(res, 'lxml')

        title_html = soup.title
        title = getattr(title_html, 'text', None)
        if title:
            title = title.replace('\n', '').strip()

        html_body = res.text

        return title, html_body, soup

    def __generate_refs(self, bs_result_set):
        for ref in bs_result_set:
            try:
                href = URL(ref.attrs['href'])

                if href.query_string:
                    continue
                if not href.is_absolute():
                    href = self.url.join(href)
                if href != self.url:
                    yield href
            except KeyError:
                continue
