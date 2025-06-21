import uuid

from src.core.memory import MemoryManager
from src.tools.file_tools import FileTools


def test_memory_remember_recall_benchmark(tmp_path, benchmark):
    mem_file = tmp_path / "memory.json"
    manager = MemoryManager(str(mem_file), auto_save=False)

    def run():
        key = str(uuid.uuid4())
        manager.remember(key, "value")
        manager.recall(key)
        manager.forget(key)

    benchmark(run)


def test_file_tools_write_read_benchmark(tmp_path, benchmark):
    tools = FileTools()
    file_path = tmp_path / "bench.txt"

    def run():
        tools.write_file(str(file_path), "hello", overwrite=True)
        tools.read_file(str(file_path))

    benchmark(run)
