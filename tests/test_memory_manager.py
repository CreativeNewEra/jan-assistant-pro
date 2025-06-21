import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import pytest

from src.core.memory import MemoryManager


def test_memory_persistence(tmp_path):
    """MemoryManager should persist data between instances."""
    # Create a temporary file path
    temp_path = tmp_path / "memory_test.db"

    with MemoryManager(str(temp_path), auto_save=False) as manager:
        assert manager.remember("greeting", "hello")
        assert manager.save_memory() is True

    # Reload manager to confirm data was saved
    with MemoryManager(str(temp_path), auto_save=False) as new_manager:
        assert new_manager.load_memory() is True
        recalled = new_manager.recall("greeting")
        assert recalled is not None
        assert recalled.get("value") == "hello"


def test_auto_save_no_deadlock(tmp_path):
    """Calling remember and recall with auto_save enabled should not deadlock."""
    temp_path = tmp_path / "memory_test.db"
    with MemoryManager(str(temp_path)) as manager:
        assert manager.remember("topic", "value") is True

        recalled = manager.recall("topic")
        assert recalled is not None
        assert recalled.get("value") == "value"


def test_memory_forget(tmp_path):
    """forget should remove entries and return False when missing."""
    path = tmp_path / "mem.db"
    with MemoryManager(str(path), auto_save=False) as manager:
        # Missing key returns False
        assert manager.forget("missing") is False

        manager.remember("foo", "bar")
        assert manager.recall("foo") is not None
        # Existing key removed
        assert manager.forget("foo") is True
        assert manager.recall("foo") is None


def test_memory_fuzzy_recall(tmp_path):
    """fuzzy_recall should return approximate matches."""
    path = tmp_path / "mem.db"
    with MemoryManager(str(path), auto_save=False) as manager:
        manager.remember("greeting", "hello world")
        manager.remember("farewell", "goodbye friend")

        keys_partial = [k for k, _ in manager.fuzzy_recall("greet")]
        assert "greeting" in keys_partial

        keys_value = [k for k, _ in manager.fuzzy_recall("hello")]
        assert "greeting" in keys_value


def test_memory_get_stats(tmp_path):
    """get_stats should report accurate counts after operations."""
    path = tmp_path / "mem.db"
    with MemoryManager(str(path), auto_save=False) as manager:
        manager.remember("a", "1", category="cat1")
        manager.remember("b", "2", category="cat1")
        manager.remember("c", "3", category="cat2")

        manager.recall("a")
        manager.recall("a")
        manager.recall("c")

        # Remove one entry
        manager.forget("b")

        stats = manager.get_stats()

        assert stats["total_entries"] == 2
        assert sorted(stats["categories"]) == sorted(["cat1", "cat2"])

        all_timestamps = stats["timestamps"].values()
        expected_oldest = min(all_timestamps)
        expected_newest = max(all_timestamps)
        assert stats["oldest_entry"] == expected_oldest
        assert stats["newest_entry"] == expected_newest
        assert stats["most_accessed"] == "a"


@pytest.mark.parametrize("max_entries,added", [(3, 2), (3, 3), (3, 4)])
def test_memory_cleanup_max_entries(tmp_path, max_entries, added):
    path = tmp_path / "mem.json"
    with MemoryManager(str(path), max_entries=max_entries, auto_save=False) as manager:
        for i in range(added):
            manager.remember(f"k{i}", f"v{i}")
        manager.save_memory()
        expected_keys = {f"k{i}" for i in range(max(0, added - max_entries), added)}
        assert set(manager.memory_data.keys()) == expected_keys
        assert len(manager.memory_data) == min(added, max_entries)
