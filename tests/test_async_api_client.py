from unittest.mock import AsyncMock, Mock, patch
import time

import asyncio
import pytest
import aiohttp

from src.core.async_api_client import AsyncAPIClient
from src.core.exceptions import APIError
from src.core.circuit_breaker import CircuitBreaker


def _create_client():
    return AsyncAPIClient(base_url="http://test", api_key="key", model="model")


def _create_cached_client():
    return AsyncAPIClient(
        base_url="http://test",
        api_key="key",
        model="model",
        cache_enabled=True,
        cache_ttl=60,
        cache_size=10,
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
async def test_chat_completion_cached():
    client = _create_cached_client()
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
            await client.chat_completion(messages)
            await client.chat_completion(messages)
            assert post.call_count == 1


@pytest.mark.asyncio
async def test_get_models_cached():
    client = _create_cached_client()
    async with client:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"data": [{"id": "1"}]})
        mock_resp.raise_for_status = Mock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_resp
        mock_cm.__aexit__.return_value = None
        with patch.object(client.session, "get", return_value=mock_cm) as get:
            await client.get_models()
            await client.get_models()
            assert get.call_count == 1


@pytest.mark.asyncio
async def test_clear_api_cache():
    client = _create_cached_client()
    async with client:
        client._cache["x"] = {"data": 1}
        assert len(client._cache) == 1
        client.clear_api_cache()
        assert len(client._cache) == 0


@pytest.mark.asyncio
async def test_circuit_breaker_blocks_calls():
    breaker = CircuitBreaker(fail_max=2, reset_timeout=1)
    client = AsyncAPIClient(
        base_url="http://test",
        api_key="key",
        model="model",
        circuit_breaker=breaker,
    )
    messages = [{"role": "user", "content": "hi"}]
    async with client:
        with patch.object(
            client.session, "post", side_effect=aiohttp.ClientError
        ) as post:
            with pytest.raises(APIError):
                await client.chat_completion(messages)
            with pytest.raises(APIError):
                await client.chat_completion(messages)
            assert post.call_count == 2
        assert breaker.state == CircuitBreaker.OPEN

        with patch.object(client.session, "post") as post:
            with pytest.raises(APIError):
                await client.chat_completion(messages)
            post.assert_not_called()

        await asyncio.sleep(1.1)
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
            await client.chat_completion(messages)
            post.assert_called_once()
        assert breaker.state == CircuitBreaker.CLOSED
