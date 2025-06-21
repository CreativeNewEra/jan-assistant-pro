"""Retry decorator utilities."""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Callable, Iterable, Type

from .exceptions import RetryableError


DEFAULT_EXCEPTIONS = (RetryableError,)


def retry(
    *,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Iterable[Type[Exception]] = DEFAULT_EXCEPTIONS,
) -> Callable:
    """Retry calling the wrapped function on specified exceptions."""

    exc_tuple = tuple(exceptions)

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                delay = initial_delay
                attempt = 0
                while True:
                    try:
                        return await func(*args, **kwargs)
                    except exc_tuple:
                        attempt += 1
                        if attempt >= max_attempts:
                            raise
                        await asyncio.sleep(delay)
                        delay *= backoff_factor

            return functools.wraps(func)(async_wrapper)

        def wrapper(*args, **kwargs):
            delay = initial_delay
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exc_tuple:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    time.sleep(delay)
                    delay *= backoff_factor

        return functools.wraps(func)(wrapper)

    return decorator


__all__ = ["retry"]

