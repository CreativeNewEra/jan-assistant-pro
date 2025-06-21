import os
import time

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


def test_write_file_atomic_failure(monkeypatch, tmp_path):
    tools = FileTools()
    file_path = tmp_path / "atomic.txt"
    file_path.write_text("original")

    def fail_replace(src, dst):
        raise RuntimeError("boom")

    monkeypatch.setattr(os, "replace", fail_replace)
    result = tools.write_file(str(file_path), "new", overwrite=True)
    assert result["success"] is False
    assert file_path.read_text() == "original"
    assert list(tmp_path.iterdir()) == [file_path]


def test_append_file_atomic_failure(monkeypatch, tmp_path):
    tools = FileTools()
    file_path = tmp_path / "append.txt"
    file_path.write_text("orig")

    def fail_replace(src, dst):
        raise RuntimeError("boom")

    monkeypatch.setattr(os, "replace", fail_replace)
    result = tools.append_file(str(file_path), "more")
    assert result["success"] is False
    assert file_path.read_text() == "orig"
    assert list(tmp_path.iterdir()) == [file_path]


def test_list_files_disk_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    tools = FileTools(disk_cache_dir=str(cache_dir), disk_cache_ttl=1)

    (tmp_path / "a.txt").write_text("1")
    result1 = tools.list_files(str(tmp_path))
    assert result1["total_files"] == 1

    (tmp_path / "b.txt").write_text("2")
    result_cached = tools.list_files(str(tmp_path))
    assert result_cached["total_files"] == 1

    time.sleep(1.1)
    result2 = tools.list_files(str(tmp_path))
    assert result2["total_files"] == 2

    result_bypass = tools.list_files(str(tmp_path), use_cache=False)
    assert result_bypass["total_files"] == 2

    (tmp_path / "c.txt").write_text("3")
    result_clear = tools.list_files(str(tmp_path), clear_cache=True)
    assert result_clear["total_files"] == 3


def test_copy_file_progress_callback(tmp_path):
    tools = FileTools()
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_bytes(b"x" * 2048)
    calls = []

    def progress(current, total):
        calls.append((current, total))

    tools.copy_file(str(src), str(dst), progress_callback=progress)
    assert dst.exists()
    assert calls
    assert calls[-1][0] == calls[-1][1]


def test_list_files_progress_callback(tmp_path):
    tools = FileTools()
    for i in range(3):
        (tmp_path / f"f{i}.txt").write_text("x")
    calls = []

    def progress(current, total):
        calls.append((current, total))

    tools.list_files(str(tmp_path), progress_callback=progress, use_cache=False)
    assert calls
    assert calls[-1][0] == calls[-1][1]
