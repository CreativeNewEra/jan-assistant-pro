import os
from src.core.app_controller import AppController
from tests.factories import ConfigFactory


def test_undo_redo_file_write(tmp_path):
    cfg = ConfigFactory(tmp_dir=tmp_path)
    controller = AppController(cfg)
    file_path = tmp_path / "undo.txt"

    controller._handle_tool_call(f"TOOL_WRITE_FILE:{file_path}|hello")
    assert file_path.read_text() == "hello"

    controller.undo_last()
    assert not file_path.exists()

    controller.redo_last()
    assert file_path.read_text() == "hello"


def test_undo_redo_memory(tmp_path):
    cfg = ConfigFactory(tmp_dir=tmp_path)
    controller = AppController(cfg)

    controller._handle_tool_call("TOOL_REMEMBER:foo|bar|general")
    assert controller.memory_manager.recall("foo")

    controller.undo_last()
    assert controller.memory_manager.recall("foo") is None

    controller.redo_last()
    mem = controller.memory_manager.recall("foo")
    assert mem and mem["value"] == "bar"
