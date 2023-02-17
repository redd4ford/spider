import functools


def use_cache(func):
    """
    Skip already crawled URLs to prevent DB override operations.
    """
    cache = set()

    @functools.wraps(func)
    async def wrapper(url, *args):
        instance = args[0]
        do = getattr(instance, 'should_use_cache', True)
        silent = getattr(instance, 'silent', False)

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
