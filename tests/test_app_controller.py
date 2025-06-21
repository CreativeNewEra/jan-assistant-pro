import os
import sys
from unittest.mock import patch

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.core.app_controller import AppController
from src.core.config import Config
from src.core.api_client import APIError


def _create_config(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        '{"api": {"base_url": "http://test", "api_key": "k", "model": "m"}, "memory": {"file": "mem"}}'
    )
    return Config(config_path=str(cfg_path))


def test_chat_with_tools_api_error_no_cache(tmp_path):
    cfg = _create_config(tmp_path)
    controller = AppController(cfg)
    with patch.object(
        controller.api_client, "chat_completion", side_effect=APIError("boom")
    ):
        message = controller._chat_with_tools("hello")
    assert "unable to reach" in message.lower()


def test_chat_with_tools_api_error_with_cached_result(tmp_path):
    cfg = _create_config(tmp_path)
    controller = AppController(cfg)
    controller.last_tool_result = "cached result"
    with patch.object(
        controller.api_client, "chat_completion", side_effect=APIError("down")
    ):
        message = controller._chat_with_tools("hello")
    assert "cached result" in message
