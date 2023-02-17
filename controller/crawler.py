import asyncio
from typing import (
    Tuple,
    Optional,
)

import httpx

from bs4 import BeautifulSoup
from yarl import URL

from db import BaseDatabase
from controller.utils.decorators import (
    log_time,
    use_cache,
)


class Crawler:
    """
    Performs crawling of a url with specified depth.
    """

    def __init__(
        self, database: BaseDatabase, start_url: str, depth: int,
        silent: bool = False, should_log_time: bool = True, should_use_cache: bool = True,
    ):
        self.client = httpx.AsyncClient()
        self.db = database
        self.url = URL(start_url)
        self.depth = depth

        self.silent = silent
        self.should_log_time = should_log_time
        self.should_use_cache = should_use_cache

    @log_time
    async def crawl(self):
        calls = 0

        @use_cache
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

    async def __load_and_parse(self, url: URL) -> Optional[Tuple[Optional[str], str, BeautifulSoup]]:
        try:
            response = await self.client.get(str(url))
        except httpx.HTTPError as exc:
            if not self.silent:
                print(f'HTTP Exception for {exc.request.url}')
            return
        except ValueError:
            return

        return self.__parsed(response)

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

    @classmethod
    def __parsed(cls, response: httpx.Response) -> Tuple[Optional[str], str, BeautifulSoup]:
        # noinspection PyTypeChecker
        soup = BeautifulSoup(response, 'lxml')

        title_html = soup.title
        title = getattr(title_html, 'text', None)
        if title:
            title = title.replace('\n', '').strip()

        html_body = response.text

        return title, html_body, soup
