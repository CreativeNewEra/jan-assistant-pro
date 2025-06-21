import os
import sys
import time

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.core.config import Config
from src.core.unified_config import UnifiedConfig


def _write_config(path, base_url):
    path.write_text(
        '{"api": {"base_url": "'
        + base_url
        + '", "api_key": "k", "model": "m"}, "memory": {"file": "mem"}, "cache": {"config": {"ttl": 1, "size": 1}}}'
    )


def test_config_reload_after_ttl(tmp_path):
    cfg_file = tmp_path / "config.json"
    _write_config(cfg_file, "http://a")
    cfg = Config(config_path=str(cfg_file))
    assert cfg.get("api.base_url") == "http://a"

    _write_config(cfg_file, "http://b")
    time.sleep(1.1)
    assert cfg.get("api.base_url") == "http://b"


def test_unified_config_reload_after_ttl(tmp_path):
    cfg_file = tmp_path / "config.json"
    _write_config(cfg_file, "http://a")
    cfg = UnifiedConfig(config_path=str(cfg_file))
    assert cfg.get("api.base_url") == "http://a"

    _write_config(cfg_file, "http://c")
    time.sleep(1.1)
    assert cfg.get("api.base_url") == "http://c"
