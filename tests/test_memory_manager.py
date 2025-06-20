import os
import tempfile
import sys

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
