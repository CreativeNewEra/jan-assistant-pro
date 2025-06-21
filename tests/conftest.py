import os
import sys
import json
import pytest

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core.api_client import APIClient
from src.core.async_api_client import AsyncAPIClient
from src.core.unified_config import UnifiedConfig
from .factories import ConfigFactory


@pytest.fixture
def api_client():
    client = APIClient(base_url="http://test", api_key="key", model="model")
    yield client
    client.close()


@pytest.fixture
def async_api_client():
    return AsyncAPIClient(base_url="http://test", api_key="key", model="model")


@pytest.fixture
def cached_async_api_client():
    return AsyncAPIClient(
        base_url="http://test",
        api_key="key",
        model="model",
        cache_enabled=True,
        cache_ttl=60,
        cache_size=10,
    )


@pytest.fixture
def temp_config(tmp_path):
    return ConfigFactory(tmp_dir=tmp_path)


@pytest.fixture
def config_factory(tmp_path):
    def _create(data=None):
        return ConfigFactory(tmp_dir=tmp_path, data=data)

    return _create


def _build_config_data(tmp_path, invalid=False):
    data = {
        "api": {
            "base_url": "http://test",
            "api_key": "k",
            "model": "m",
            "timeout": 30,
        },
        "memory": {"file": str(tmp_path / "mem.json")},
    }
    if invalid:
        data["api"]["timeout"] = "bad"
    return data


@pytest.fixture(params=["default", "invalid"])
def mock_config(tmp_path, request):
    """Return Config object for different scenarios."""
    data = _build_config_data(tmp_path, invalid=request.param == "invalid")
    return ConfigFactory(tmp_dir=tmp_path, data=data)


@pytest.fixture(params=["default", "invalid"])
def mock_unified_config(tmp_path, request):
    """Return UnifiedConfig object for different scenarios."""
    data = _build_config_data(tmp_path, invalid=request.param == "invalid")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data))
    return UnifiedConfig(config_path=str(config_path))


@pytest.fixture
def env_timeout(monkeypatch):
    """Environment setting that overrides API timeout."""
    monkeypatch.setenv("JAN_ASSISTANT_API_TIMEOUT", "45")


@pytest.fixture
def default_config_data(tmp_path):
    """Return default configuration data dictionary."""
    return _build_config_data(tmp_path)
