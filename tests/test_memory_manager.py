import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.memory import MemoryManager


def test_memory_persistence(tmp_path):
    """MemoryManager should persist data between instances."""
    # Create a temporary file path
    temp_path = tmp_path / "memory_test.db"

    manager = MemoryManager(str(temp_path), auto_save=False)
    assert manager.remember("greeting", "hello")
    assert manager.save_memory() is True

    # Reload manager to confirm data was saved
    new_manager = MemoryManager(str(temp_path), auto_save=False)
    assert new_manager.load_memory() is True
    recalled = new_manager.recall("greeting")
    assert recalled is not None
    assert recalled.get("value") == "hello"


def test_auto_save_no_deadlock(tmp_path):
    """Calling remember and recall with auto_save enabled should not deadlock."""
    temp_path = tmp_path / "memory_test.db"
    manager = MemoryManager(str(temp_path))

    assert manager.remember("topic", "value") is True

    recalled = manager.recall("topic")
    assert recalled is not None
    assert recalled.get("value") == "value"


def test_memory_forget(tmp_path):
    """forget should remove entries and return False when missing."""
    path = tmp_path / "mem.db"
    manager = MemoryManager(str(path), auto_save=False)

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
    manager = MemoryManager(str(path), auto_save=False)

    manager.remember("greeting", "hello world")
    manager.remember("farewell", "goodbye friend")

    keys_partial = [k for k, _ in manager.fuzzy_recall("greet")]
    assert "greeting" in keys_partial

    keys_value = [k for k, _ in manager.fuzzy_recall("hello")]
    assert "greeting" in keys_value


def test_memory_get_stats(tmp_path):
    """get_stats should report accurate counts after operations."""
    path = tmp_path / "mem.db"
    manager = MemoryManager(str(path), auto_save=False)

    manager.remember("a", "1", category="cat1")
    manager.remember("b", "2", category="cat1")
    manager.remember("c", "3", category="cat2")

    ts_a = manager.memory_data["a"]["timestamp"]
    ts_b = manager.memory_data["b"]["timestamp"]
    ts_c = manager.memory_data["c"]["timestamp"]

    # Access some entries to update counts
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
