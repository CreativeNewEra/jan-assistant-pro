import os
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core.unified_config import UnifiedConfig


def test_config_reload_after_ttl(config_factory):
    data = {
        "api": {"base_url": "http://a", "api_key": "k", "model": "m"},
        "memory": {"file": "mem"},
        "cache": {"config": {"ttl": 1, "size": 1}},
    }
    cfg = config_factory(data=data)
    cfg_file = Path(cfg.config_path)
    assert cfg.get("api.base_url") == "http://a"

    data["api"]["base_url"] = "http://b"
    cfg_file.write_text(json.dumps(data))
    time.sleep(1.1)
    assert cfg.get("api.base_url") == "http://b"


def test_unified_config_reload_after_ttl(config_factory):
    data = {
        "api": {"base_url": "http://a", "api_key": "k", "model": "m"},
        "memory": {"file": "mem"},
        "cache": {"config": {"ttl": 1, "size": 1}},
    }
    cfg = config_factory(data=data)
    cfg_file = Path(cfg.config_path)
    uni_cfg = UnifiedConfig(config_path=str(cfg_file))
    assert uni_cfg.get("api.base_url") == "http://a"

    data["api"]["base_url"] = "http://c"
    cfg_file.write_text(json.dumps(data))
    time.sleep(1.1)
    assert uni_cfg.get("api.base_url") == "http://c"
