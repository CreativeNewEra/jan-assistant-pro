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


def test_write_file_no_overwrite_existing(tmp_path):
    tools = FileTools()
    file_path = tmp_path / "test.txt"
    file_path.write_text("original")
    result = tools.write_file(str(file_path), "new", overwrite=False)
    assert result["success"] is False
    assert file_path.read_text() == "original"


def test_list_files_basic_and_hidden(tmp_path):
    tools = FileTools()

    (tmp_path / "dir_a").mkdir()
    (tmp_path / "dir_b").mkdir()
    (tmp_path / "file1.txt").write_text("1")
    (tmp_path / "file2.txt").write_text("2")
    (tmp_path / ".hidden.txt").write_text("hidden")

    result = tools.list_files(str(tmp_path))
    assert result["success"] is True
    assert result["total_files"] == 2
    assert result["total_directories"] == 2
    file_names = {f["name"] for f in result["files"]}
    dir_names = {d["name"] for d in result["directories"]}
    assert file_names == {"file1.txt", "file2.txt"}
    assert dir_names == {"dir_a", "dir_b"}

    result_hidden = tools.list_files(str(tmp_path), include_hidden=True)
    hidden_names = {f["name"] for f in result_hidden["files"]}
    assert ".hidden.txt" in hidden_names


def test_delete_file_missing(tmp_path):
    tools = FileTools()
    target = tmp_path / "missing.txt"
    result = tools.delete_file(str(target))
    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_restricted_path_access(tmp_path):
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    file_path = restricted_dir / "file.txt"
    file_path.write_text("content")
    tools = FileTools(restricted_paths=[str(restricted_dir)])

    result = tools.read_file(str(file_path))
    assert result["success"] is False
    assert "restricted" in result["error"]

