import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.memory import EnhancedMemoryManager


def test_sqlite_persistence(tmp_path):
    db_path = tmp_path / "memory.sqlite"
    manager = EnhancedMemoryManager(str(db_path), max_entries=5)
    assert manager.remember("foo", "bar")

    new_manager = EnhancedMemoryManager(str(db_path), max_entries=5)
    recalled = new_manager.recall("foo")
    assert recalled is not None
    assert recalled["value"] == "bar"


def test_access_statistics(tmp_path):
    db_path = tmp_path / "stats.sqlite"
    manager = EnhancedMemoryManager(str(db_path))
    manager.remember("hello", "world")

    assert manager.recall("hello") is not None
    second = manager.recall("hello")
    # After first recall, access_count is incremented once; recall returns previous value
    updated = manager.recall("hello")
    assert updated is not None
    assert updated["access_count"] == 2


def test_fuzzy_search(tmp_path):
    db_path = tmp_path / "search.sqlite"
    manager = EnhancedMemoryManager(str(db_path))
    manager.remember("greeting", "hello world")
    manager.remember("farewell", "goodbye")

    results = manager.fuzzy_search("greet")
    keys = [r["key"] for r in results]
    assert "greeting" in keys
