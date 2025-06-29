import platform
import time
from unittest.mock import patch

import pytest

pytest.importorskip("psutil", reason="psutil is required for system metrics tests")

from src.tools.system_tools import SystemTools


def test_check_network_connectivity_success():
    tools = SystemTools()
    mock_result = {"success": True, "return_code": 0, "stdout": "ok", "stderr": ""}
    with patch.object(tools, "run_command", return_value=mock_result) as run_cmd:
        result = tools.check_network_connectivity("example.com")
        run_cmd.assert_called_once()
    assert result["success"] is True
    assert result["connected"] is True
    assert result["host"] == "example.com"


def test_check_network_connectivity_failure_nonzero():
    tools = SystemTools()
    mock_result = {"success": True, "return_code": 1, "stderr": "unreachable"}
    with patch.object(tools, "run_command", return_value=mock_result):
        result = tools.check_network_connectivity("example.com")
    assert result["success"] is False
    assert result["connected"] is False
    assert "unreachable" in result["error"]


def test_check_network_connectivity_failure_error():
    tools = SystemTools()
    mock_result = {"success": False, "return_code": 1, "stderr": "timeout"}
    with patch.object(tools, "run_command", return_value=mock_result):
        result = tools.check_network_connectivity("example.com")
    assert result["success"] is False
    assert result["connected"] is False
    assert "timeout" in result["error"]


def test_check_network_connectivity_failure_result_error():
    tools = SystemTools()
    mock_result = {"success": False, "error": "not allowed"}
    with patch.object(tools, "run_command", return_value=mock_result):
        result = tools.check_network_connectivity("example.com")
    assert result["success"] is False
    assert result["connected"] is False
    assert "not allowed" in result["error"]


@pytest.mark.parametrize("mock_unified_config", ["default"], indirect=True)
def test_check_network_connectivity_with_default_config(mock_unified_config):
    cfg = mock_unified_config
    tools = SystemTools(allowed_commands=cfg.get("security.allowed_commands"))
    mock_result = {"success": True, "return_code": 0, "stdout": "ok", "stderr": ""}
    with patch.object(tools, "run_command", return_value=mock_result) as run_cmd:
        result = tools.check_network_connectivity("example.com")
        run_cmd.assert_called_once()
    assert result["success"] is True
    assert result["connected"] is True


def test_get_system_info_disk_cache(monkeypatch, tmp_path):
    cache_dir = tmp_path / "cache"
    tools = SystemTools(disk_cache_dir=str(cache_dir), disk_cache_ttl=1)

    monkeypatch.setattr(platform, "platform", lambda: "first")
    res1 = tools.get_system_info()
    assert res1["platform"] == "first"

    monkeypatch.setattr(platform, "platform", lambda: "second")
    res_cached = tools.get_system_info()
    assert res_cached["platform"] == "first"

    time.sleep(1.1)
    res2 = tools.get_system_info()
    assert res2["platform"] == "second"

    monkeypatch.setattr(platform, "platform", lambda: "third")
    res_bypass = tools.get_system_info(use_cache=False)
    assert res_bypass["platform"] == "third"

    monkeypatch.setattr(platform, "platform", lambda: "fourth")
    res_clear = tools.get_system_info(clear_cache=True)
    assert res_clear["platform"] == "fourth"


def test_list_directory(tmp_path):
    tools = SystemTools()

    (tmp_path / "d1").mkdir()
    (tmp_path / "f1.txt").write_text("x")

    result = tools.list_directory(str(tmp_path))
    assert result["success"] is True
    names_files = {f["name"] for f in result["files"]}
    names_dirs = {d["name"] for d in result["directories"]}
    assert "f1.txt" in names_files
    assert "d1" in names_dirs


def test_list_directory_progress_callback(tmp_path):
    tools = SystemTools()
    (tmp_path / "d1").mkdir()
    (tmp_path / "f1.txt").write_text("x")
    calls = []

    def progress(current, total):
        calls.append((current, total))

    tools.list_directory(str(tmp_path), progress_callback=progress)
    assert calls
    assert calls[-1][0] == calls[-1][1]


def test_list_directory_invalid(tmp_path):
    tools = SystemTools()
    res = tools.list_directory(str(tmp_path / "nope"))
    assert res["success"] is False
