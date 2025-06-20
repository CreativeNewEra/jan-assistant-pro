import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core.unified_config import UnifiedConfig


def test_env_override_int(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"api": {"base_url": "http://a", "api_key": "k", "model": "m", "timeout": 30}, "memory": {"file": "mem"}}'
    )

    monkeypatch.setenv("JAN_ASSISTANT_API_TIMEOUT", "45")
    cfg = UnifiedConfig(config_path=str(config_file))
    assert cfg.get("api.timeout") == 45


def test_env_file_loading(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"api": {"base_url": "http://default", "api_key": "k", "model": "m"}, "memory": {"file": "mem"}}'
    )
    env_file = tmp_path / ".env"
    env_file.write_text("JAN_ASSISTANT_API_BASE_URL=http://envfile")

    cfg = UnifiedConfig(config_path=str(config_file), env_file=str(env_file))
    assert cfg.get("api.base_url") == "http://envfile"
