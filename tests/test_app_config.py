import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core.app_config import AppConfig


def test_app_config_load_env_override(monkeypatch, tmp_path):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(
        json.dumps({"api": {"base_url": "http://file", "api_key": "k", "model": "m"}, "ui": {"theme": "light"}})
    )
    monkeypatch.setenv("JAN_ASSISTANT_CONFIG_FILE", str(cfg_file))
    monkeypatch.setenv("JAN_ASSISTANT_API_BASE_URL", "http://env")
    config = AppConfig.load()
    assert config.api.base_url == "http://env"
    assert config.ui.theme == "light"
    assert config.api.api_key == "k"


def test_app_config_defaults(monkeypatch):
    monkeypatch.delenv("JAN_ASSISTANT_CONFIG_FILE", raising=False)
    config = AppConfig.load()
    assert config.api.base_url == "http://127.0.0.1:1337/v1"
    assert config.api.api_key == "124578"
