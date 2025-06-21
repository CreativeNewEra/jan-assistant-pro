from unittest.mock import AsyncMock, Mock, patch

import asyncio
import pytest
import aiohttp

from src.core.cache import DiskCache

from src.core.async_api_client import AsyncAPIClient
from src.core.exceptions import APIError


def _create_client(tmp_path=None):
    kwargs = {}
    if tmp_path is not None:
        kwargs = {
            "cache_size": 2,
            "cache_ttl": 1,
            "disk_cache": DiskCache(str(tmp_path), ttl=1),
        }
    return AsyncAPIClient(
        base_url="http://test", api_key="key", model="model", **kwargs
    )


@pytest.mark.asyncio
async def test_chat_completion_success():
    client = _create_client()
    messages = [{"role": "user", "content": "hi"}]
    async with client:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "hello"}}]}
        )
        mock_resp.raise_for_status = Mock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_resp
        mock_cm.__aexit__.return_value = None
        with patch.object(client.session, "post", return_value=mock_cm) as post:
            response = await client.chat_completion(messages)
            post.assert_called_once()
            mock_resp.raise_for_status.assert_called_once()
    assert response["choices"][0]["message"]["content"] == "hello"


@pytest.mark.asyncio
async def test_chat_completion_timeout():
    client = _create_client()
    messages = [{"role": "user", "content": "hi"}]
    async with client:
        with patch.object(client.session, "post", side_effect=asyncio.TimeoutError):
            with pytest.raises(APIError):
                await client.chat_completion(messages)


@pytest.mark.asyncio
async def test_chat_completion_client_error():
    client = _create_client()
    messages = [{"role": "user", "content": "hi"}]
    async with client:
        with patch.object(client.session, "post", side_effect=aiohttp.ClientError):
            with pytest.raises(APIError):
                await client.chat_completion(messages)


@pytest.mark.asyncio
async def test_get_models_success():
    client = _create_client()
    async with client:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"data": [{"id": "1"}]})
        mock_resp.raise_for_status = Mock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_resp
        mock_cm.__aexit__.return_value = None
        with patch.object(client.session, "get", return_value=mock_cm) as get:
            models = await client.get_models()
            get.assert_called_once()
    assert models == [{"id": "1"}]


@pytest.mark.asyncio
async def test_health_check_failure():
    client = _create_client()
    with patch.object(client, "chat_completion", side_effect=APIError("fail")):
        result = await client.health_check()
    assert result is False


@pytest.mark.asyncio
async def test_chat_completion_cache(tmp_path):
    client = _create_client(tmp_path)
    messages = [{"role": "user", "content": "hi"}]
    async with client:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={"choices": [{"message": {"content": "ok"}}]}
        )
        mock_resp.raise_for_status = Mock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_resp
        mock_cm.__aexit__.return_value = None
        with patch.object(client.session, "post", return_value=mock_cm) as post:
            r1 = await client.chat_completion(messages)
            r2 = await client.chat_completion(messages)
            post.assert_called_once()
    assert r1 == r2
