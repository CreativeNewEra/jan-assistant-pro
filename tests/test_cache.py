import json
import time
from unittest.mock import patch

import pytest

from src.core.api_client import APIClient
from src.core.cache import DiskCache
from src.core.unified_config import UnifiedConfig


def test_lru_cache_eviction_and_ttl(tmp_path):
    client = APIClient(
        base_url="http://test",
        api_key="k",
        model="m",
        cache_size=2,
        cache_ttl=1,
        disk_cache_dir=str(tmp_path),
    )

    messages1 = [{"role": "user", "content": "a"}]
    messages2 = [{"role": "user", "content": "b"}]
    messages3 = [{"role": "user", "content": "c"}]

    with client:

        class FakeResp:
            def __init__(self, data):
                self._data = data

            def raise_for_status(self):
                pass

            def json(self):
                return self._data

        fake_resp1 = FakeResp({"id": 1})
        fake_resp2 = FakeResp({"id": 2})
        fake_resp3 = FakeResp({"id": 3})

        with patch.object(
            client._async_client.session,
            "post",
            side_effect=[fake_resp1, fake_resp2, fake_resp3, fake_resp2],
        ) as post:
            r1 = client.chat_completion(messages1)
            r2 = client.chat_completion(messages2)
            assert post.call_count == 2
            assert client.chat_completion(messages1) == r1
            assert post.call_count == 2
            client.chat_completion(messages3)
            assert post.call_count == 3
            assert client.chat_completion(messages2) == r2
            assert post.call_count == 3
            time.sleep(1.1)
            client.chat_completion(messages2)
            assert post.call_count == 4


def test_disk_cache_read_write_expiry(tmp_path):
    cache = DiskCache(str(tmp_path), ttl=0.5)
    cache.set("k", {"v": 1})
    assert cache.get("k") == {"v": 1}
    time.sleep(0.6)
    assert cache.get("k") is None


def test_config_reload_after_ttl(tmp_path):
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(
        json.dumps(
            {
                "api": {"base_url": "http://one", "api_key": "k", "model": "m"},
                "memory": {"file": "mem.json"},
            }
        )
    )

    cfg = UnifiedConfig(config_path=str(cfg_path), reload_ttl=0.5)
    assert cfg.get("api.base_url") == "http://one"
    cfg_path.write_text(
        json.dumps(
            {
                "api": {"base_url": "http://two", "api_key": "k", "model": "m"},
                "memory": {"file": "mem.json"},
            }
        )
    )
    time.sleep(0.6)
    assert cfg.get("api.base_url") == "http://two"
