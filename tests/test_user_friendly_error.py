import os

from src.tools.file_tools import FileTools


def test_write_file_read_only_directory(monkeypatch, tmp_path):
    tools = FileTools()
    read_only_dir = tmp_path / "ro"
    read_only_dir.mkdir()
    file_path = read_only_dir / "file.txt"

    def deny_replace(src, dst):
        raise PermissionError("read only")

    monkeypatch.setattr(os, "replace", deny_replace)
    result = tools.write_file(str(file_path), "data")
    assert result["success"] is False
    assert "user_error" in result
    assert any(
        "permissions" in s for s in result["user_error"]["suggestions"]
    )
