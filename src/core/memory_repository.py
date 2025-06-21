from __future__ import annotations

"""Repository pattern for memory persistence."""

import asyncio
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .storage import StorageInterface


@dataclass
class Memory:
    """Simple memory record."""

    id: str
    key: str
    value: str
    category: str = "general"
    timestamp: str = ""
    access_count: int = 0

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryRepository:
    """Persist memories using a :class:`StorageInterface`."""

    def __init__(self, storage: StorageInterface) -> None:
        self.storage = storage
        self.index_key = "memory:index"

    async def _load_index(self) -> List[str]:
        data = await asyncio.to_thread(self.storage.load, self.index_key)
        return data if isinstance(data, list) else []

    async def _save_index(self, index: List[str]) -> None:
        await asyncio.to_thread(self.storage.save, self.index_key, index)

    async def save(self, memory: Memory) -> None:
        await asyncio.to_thread(
            self.storage.save, f"memory:{memory.id}", memory.dict()
        )
        index = await self._load_index()
        if memory.id not in index:
            index.append(memory.id)
            await self._save_index(index)
        await asyncio.to_thread(
            self.storage.save, f"memory_key:{memory.key}", memory.id
        )

    async def find_by_key(self, key: str) -> Optional[Memory]:
        mem_id = await asyncio.to_thread(self.storage.load, f"memory_key:{key}")
        if mem_id is None:
            return None
        data = await asyncio.to_thread(self.storage.load, f"memory:{mem_id}")
        return Memory(**data) if data else None

    async def search(self, query: str) -> List[Memory]:
        index = await self._load_index()
        results: List[Memory] = []
        q = query.lower()
        for mem_id in index:
            data = await asyncio.to_thread(self.storage.load, f"memory:{mem_id}")
            if not data:
                continue
            if q in data.get("key", "").lower() or q in data.get("value", "").lower():
                results.append(Memory(**data))
        return results

