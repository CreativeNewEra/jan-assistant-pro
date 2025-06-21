import asyncio

from src.core.memory_repository import Memory, MemoryRepository
from src.core.storage import JSONStorage


async def test_memory_repository_save_and_find(tmp_path):
    storage = JSONStorage(str(tmp_path / "mem.json"))
    repo = MemoryRepository(storage)
    mem = Memory(id="1", key="foo", value="bar")
    await repo.save(mem)
    found = await repo.find_by_key("foo")
    assert found is not None
    assert found.value == "bar"


async def test_memory_repository_search(tmp_path):
    storage = JSONStorage(str(tmp_path / "mem.json"))
    repo = MemoryRepository(storage)
    await repo.save(Memory(id="1", key="foo", value="bar"))
    await repo.save(Memory(id="2", key="hello", value="world"))

    results = await repo.search("foo")
    assert any(m.key == "foo" for m in results)

    results = await repo.search("world")
    assert any(m.key == "hello" for m in results)

