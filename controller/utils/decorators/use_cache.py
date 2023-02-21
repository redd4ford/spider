import functools

from controller.utils.loggers import logger


def use_cache(func):
    """
    Skip already crawled URLs to prevent DB override operations.
    """
    cache = set()

    @functools.wraps(func)
    async def wrapper(*args):
        instance, url, depth = args
        do = getattr(instance, 'should_use_cache', True)
        silent = getattr(instance, 'silent', False)

        if do:
            if url not in cache:
                cache.add(url)
                await func(*args)
            else:
                if not silent:
                    logger.warning(f'Found {url} in cache. Skipping...')
        else:
            await func(*args)
    return wrapper
