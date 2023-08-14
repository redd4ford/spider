import asyncio
from typing import (
    Optional,
    Tuple,
)

import bs4
import httpx
from yarl import URL

from crawler.decorators import (
    log_time,
    use_cache,
)
from controllers.core.loggers import logger
from db.core import BaseDatabase


class Crawler:
    """
    Performs crawling of a URL with specified depth level.
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

        self.successful_crawls_counter = 0
        self.total_calls = 0

    @log_time
    async def crawl(self):
        """
        Main crawling method. The whole procedure is recursive and is performed in load().
        """
        try:
            await self.db.connect()
            self.db.create_table(check_first=True, silent=True)
        except Exception as exc:
            logger.error(f'Database connection error: {exc}')
            return

        try:
            await self.load(self.url, 0)
        finally:
            await self.client.aclose()
            await self.db.disconnect()
            logger.crawl_ok(
                f'Done. (crawled: {self.successful_crawls_counter}, '
                f'total calls: {self.total_calls})'
            )

    @use_cache
    async def load(self, url: URL, level: int):
        """
        Perform crawling procedure on the current :param level: and generate
        deeper crawling tasks, if :param level: is less than the specified depth.
        """
        self.total_calls += 1
        try:
            title, html_body, soup = await self.__load_and_parse(url)
            self.successful_crawls_counter += 1
        except TypeError:
            logger.crawl_info(f'Cannot download URL: {url}.')
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
        todos = [self.load(ref, level + 1) for ref in refs]
        await asyncio.gather(*todos)

    async def __load_and_parse(self, url: URL) -> Optional[
        Tuple[Optional[str], str, bs4.BeautifulSoup]
    ]:
        """
        Async request of :param url: and response parsing.
        """
        try:
            response = await self.client.get(str(url))
        except httpx.HTTPError as exc:
            logger.crawl_info(f'HTTP Exception for {exc.request.url}')
            return
        except ValueError:
            return

        return self.__parsed(response)

    def __generate_refs(self, bs_result_set: bs4.ResultSet):
        """
        Find hrefs in the current page to go deeper.
        """
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
    def __parsed(cls, response: httpx.Response) -> Tuple[
        Optional[str], str, bs4.BeautifulSoup
    ]:
        """
        Extract html_body and title from the :param response:.
        """
        # noinspection PyTypeChecker
        soup = bs4.BeautifulSoup(response, 'lxml')

        title_html = soup.title
        title = getattr(title_html, 'text', None)
        if title:
            title = title.replace('\n', '').strip()

        html_body = response.text

        return title, html_body, soup
