import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core.unified_config import UnifiedConfig
import pytest


@pytest.mark.parametrize("mock_unified_config", ["default"], indirect=True)
def test_env_override_int(env_timeout, mock_unified_config):
    cfg = mock_unified_config
    assert cfg.get("api.timeout") == 45


def test_env_file_loading(default_config_data, tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(default_config_data))
    env_file = tmp_path / ".env"
    env_file.write_text("JAN_ASSISTANT_API_BASE_URL=http://envfile")

    cfg = UnifiedConfig(config_path=str(config_file), env_file=str(env_file))
    assert cfg.get("api.base_url") == "http://envfile"

