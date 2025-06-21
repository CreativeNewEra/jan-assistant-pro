import time

import pytest

from src.core.cache import (
    MEMORY_LRU_CACHE,
    MEMORY_TTL_CACHE,
    DiskCache,
    clear_memory_caches,
)


def test_disk_cache_expiration(tmp_path):
    cache = DiskCache(str(tmp_path), default_ttl=1)
    cache.set("a", 123)
    assert cache.get("a") == 123
    time.sleep(1.1)
    assert cache.get("a") is None


def test_clear_memory_caches():
    MEMORY_LRU_CACHE["x"] = 1
    MEMORY_TTL_CACHE["y"] = 2
    clear_memory_caches()
    assert len(MEMORY_LRU_CACHE) == 0
    assert len(MEMORY_TTL_CACHE) == 0


@pytest.mark.parametrize(
    "ttl,sleep,expected",
    [
        (None, 0, 123),  # default ttl
        (0, 0, 123),  # immediate expiration
        (-1, 0, None),  # negative ttl should expire
        (1, 0.5, 123),  # before expiration
        (1, 1.1, None),  # after expiration
    ],
)
def test_disk_cache_ttl_edge_cases(tmp_path, ttl, sleep, expected):
    cache = DiskCache(str(tmp_path), default_ttl=1)
    cache.set("a", 123, ttl=ttl)
    if sleep:
        time.sleep(sleep)
    assert cache.get("a") == expected
