import json
import os
import time
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """Simple LRU cache with TTL support."""

    def __init__(self, max_size: int = 128, ttl: float = 60.0) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self.store: "OrderedDict[str, tuple[Any, float]]" = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self.store:
            value, ts = self.store[key]
            if time.time() - ts < self.ttl:
                self.store.move_to_end(key)
                return value
            del self.store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = (value, time.time())
        if len(self.store) > self.max_size:
            self.store.popitem(last=False)


class DiskCache:
    """Disk-based cache with TTL."""

    def __init__(self, cache_dir: str, ttl: float = 60.0) -> None:
        self.cache_dir = cache_dir
        self.ttl = ttl
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{hash(key)}.json")

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if os.path.exists(path):
            if time.time() - os.path.getmtime(path) < self.ttl:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            os.remove(path)
        return None

    def set(self, key: str, value: Any) -> None:
        path = self._path(key)
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(value, f)
        os.replace(tmp, path)
