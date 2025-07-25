import os
import sys
from unittest.mock import patch

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.core.app_controller import AppController
from src.core.exceptions import APIError


import pytest


@pytest.mark.parametrize("mock_config", ["default"], indirect=True)
def test_chat_with_tools_api_error_no_cache(mock_config):
    cfg = mock_config
    controller = AppController(cfg)
    with patch.object(
        controller.api_client, "chat_completion", side_effect=APIError("boom")
    ):
        message = controller._chat_with_tools("hello")
    assert "unable to reach" in message.lower()


@pytest.mark.parametrize("mock_config", ["default"], indirect=True)
def test_chat_with_tools_api_error_with_cached_result(mock_config):
    cfg = mock_config
    controller = AppController(cfg)
    controller.last_tool_result = "cached result"
    with patch.object(
        controller.api_client, "chat_completion", side_effect=APIError("down")
    ):
        message = controller._chat_with_tools("hello")
    assert "cached result" in message
