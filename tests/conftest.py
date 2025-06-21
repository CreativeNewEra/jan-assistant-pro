import os
import sys
import pytest

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.core.api_client import APIClient
from src.core.async_api_client import AsyncAPIClient
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
