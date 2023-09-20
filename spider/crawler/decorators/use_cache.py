import functools
from typing import (
    Any,
    Callable,
)

from spider.controllers.core.loggers import logger


def use_cache(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Skip already crawled URLs to prevent DB overrides during current crawling operation.
    """
    cache = set()

    @functools.wraps(func)
    async def wrapper(*args: Any):
        instance, url, depth = args
        do = getattr(instance, 'should_use_cache', True)

        if do:
            if url not in cache:
                cache.add(url)
                await func(*args)
            else:
                logger.crawl_info(f'Found {url} in cache. Skipping...')
        else:
            await func(*args)
    return wrapper
