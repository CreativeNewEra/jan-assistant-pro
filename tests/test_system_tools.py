from unittest.mock import patch

from src.core.config import Config
from src.tools.system_tools import SystemTools


def test_check_network_connectivity_success():
    tools = SystemTools()
    mock_result = {'success': True, 'return_code': 0, 'stdout': 'ok', 'stderr': ''}
    with patch.object(tools, "run_command", return_value=mock_result) as run_cmd:
        result = tools.check_network_connectivity("example.com")
        run_cmd.assert_called_once()
    assert result["success"] is True
    assert result["connected"] is True
    assert result["host"] == "example.com"


def test_check_network_connectivity_failure_nonzero():
    tools = SystemTools()
    mock_result = {'success': True, 'return_code': 1, 'stderr': 'unreachable'}
    with patch.object(tools, "run_command", return_value=mock_result):
        result = tools.check_network_connectivity("example.com")
    assert result["success"] is False
    assert result["connected"] is False
    assert "unreachable" in result["error"]


def test_check_network_connectivity_failure_error():
    tools = SystemTools()
    mock_result = {'success': False, 'return_code': 1, 'stderr': 'timeout'}
    with patch.object(tools, "run_command", return_value=mock_result):
        result = tools.check_network_connectivity("example.com")
    assert result["success"] is False
    assert result["connected"] is False
    assert "timeout" in result["error"]


def test_check_network_connectivity_failure_result_error():
    tools = SystemTools()
    mock_result = {'success': False, 'error': 'not allowed'}
    with patch.object(tools, "run_command", return_value=mock_result):
        result = tools.check_network_connectivity("example.com")
    assert result["success"] is False
    assert result["connected"] is False
    assert "not allowed" in result["error"]


def test_check_network_connectivity_with_default_config(tmp_path):
    cfg = Config(config_path=str(tmp_path / "config.json"))
    tools = SystemTools(allowed_commands=cfg.get("security.allowed_commands"))
    assert "ping" in tools.allowed_commands
    mock_result = {'success': True, 'return_code': 0, 'stdout': 'ok', 'stderr': ''}
    with patch.object(tools, "run_command", return_value=mock_result) as run_cmd:
        result = tools.check_network_connectivity("example.com")
        run_cmd.assert_called_once()
    assert result["success"] is True
    assert result["connected"] is True
