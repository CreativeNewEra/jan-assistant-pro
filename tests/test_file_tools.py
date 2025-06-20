import os
from src.tools.file_tools import FileTools


def test_write_file_created_flag_new(tmp_path):
    tools = FileTools()
    file_path = tmp_path / "test.txt"
    result = tools.write_file(str(file_path), "content", overwrite=True)
    assert result["created"] is True
    assert file_path.exists()


def test_write_file_created_flag_overwrite(tmp_path):
    tools = FileTools()
    file_path = tmp_path / "test.txt"
    file_path.write_text("old")
    result = tools.write_file(str(file_path), "new", overwrite=True)
    assert result["created"] is False
    assert file_path.read_text() == "new"
