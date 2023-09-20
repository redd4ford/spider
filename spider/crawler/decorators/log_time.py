import functools
import time
from typing import (
    Any,
    Callable,
)

from spider.controllers.core.loggers import logger


def log_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Measure the elapsed time of a function/method.
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        instance = args[0]
        do = getattr(instance, 'should_log_time', True)

        start_time = time.perf_counter()
        await func(*args, **kwargs)
        finish_time = time.perf_counter()

        if do:
            logger.crawl_ok(f'Elapsed time: {finish_time - start_time}')
    return wrapper
