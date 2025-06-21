"""Simple caching utilities for Jan Assistant Pro."""

from __future__ import annotations

import pickle
import threading
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

from cachetools import LRUCache, TTLCache

from .utils import thread_safe

# ---------------------------------------------------------------------------
# In-memory caches
# ---------------------------------------------------------------------------

# Default caches for general use. Size and ttl are conservative so they work in
# most environments but can be overridden when needed.
MEMORY_LRU_CACHE = LRUCache(maxsize=128)
MEMORY_TTL_CACHE = TTLCache(maxsize=128, ttl=300)


def clear_memory_caches() -> None:
    """Clear both default in-memory caches."""
    MEMORY_LRU_CACHE.clear()
    MEMORY_TTL_CACHE.clear()


# ---------------------------------------------------------------------------
# Disk cache implementation
# ---------------------------------------------------------------------------


class DiskCache:
    """Very small disk-based cache using pickle files with TTL metadata."""

    def __init__(self, cache_dir: str, default_ttl: int = 3600) -> None:
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        """Return a safe path for ``key``."""
        hashed = sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{hashed}.pkl"

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds."""
        expires_at = time.time() + (ttl or self.default_ttl)
        path = self._path_for_key(key)
        data = {"expires_at": expires_at, "value": value}
        with thread_safe(self._lock), open(path, "wb") as f:
            pickle.dump(data, f)

    def get(self, key: str) -> Any | None:
        """Retrieve ``key`` if present and not expired."""
        path = self._path_for_key(key)
        if not path.exists():
            return None
        with thread_safe(self._lock):
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
            except Exception:
                # Corrupt cache; remove it
                path.unlink(missing_ok=True)
                return None
        if data.get("expires_at", 0) < time.time():
            path.unlink(missing_ok=True)
            return None
        return data.get("value")

    def delete(self, key: str) -> None:
        """Remove ``key`` from the cache."""
        path = self._path_for_key(key)
        with thread_safe(self._lock):
            if path.exists():
                path.unlink()

    def clear(self) -> None:
        """Clear the entire disk cache."""
        with thread_safe(self._lock):
            for file in self.cache_dir.glob("*.pkl"):
                file.unlink()


__all__ = [
    "LRUCache",
    "TTLCache",
    "MEMORY_LRU_CACHE",
    "MEMORY_TTL_CACHE",
    "clear_memory_caches",
    "DiskCache",
]
