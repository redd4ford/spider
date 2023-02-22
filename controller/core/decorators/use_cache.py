import functools

from controller.core.loggers import logger


def use_cache(func):
    """
    Skip already crawled URLs to prevent DB override operations.
    """
    cache = set()

    @functools.wraps(func)
    async def wrapper(*args):
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
