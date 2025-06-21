import threading
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def thread_safe(lock: threading.Lock) -> Iterator[None]:
    """Acquire ``lock`` for the duration of the context."""
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
