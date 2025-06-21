import os
import sys
import threading

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.core.utils import thread_safe


def test_thread_safe_releases_lock_on_exception():
    lock = threading.Lock()
    with pytest.raises(RuntimeError):
        with thread_safe(lock):
            assert lock.locked()
            raise RuntimeError("boom")
    # lock should be released even after exception
    assert lock.acquire(blocking=False)
    lock.release()
