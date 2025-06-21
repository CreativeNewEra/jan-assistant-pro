from unittest.mock import AsyncMock, patch
import time

import pytest


from src.core.api_client import APIClient
from src.core.exceptions import APIError
from src.core.circuit_breaker import CircuitBreaker


def test_chat_completion_success(api_client):
    messages = [{"role": "user", "content": "hi"}]
    async_mock = AsyncMock(
        return_value={"choices": [{"message": {"content": "hello"}}]}
    )
    with patch.object(api_client._async_client, "chat_completion", async_mock):
        response = api_client.chat_completion(messages)
        async_mock.assert_awaited_once_with(
            messages, stream=False, temperature=0.7, max_tokens=None
        )
    assert response["choices"][0]["message"]["content"] == "hello"
    assert api_client.extract_content(response) == "hello"
    api_client.close()
    assert api_client._async_client.session is None


def test_chat_completion_model_not_loaded(api_client):
    messages = [{"role": "user", "content": "hi"}]
    async_mock = AsyncMock(side_effect=APIError("Model is not loaded"))
    with patch.object(api_client._async_client, "chat_completion", async_mock):
        with pytest.raises(APIError) as exc:
            api_client.chat_completion(messages)
    assert "Model is not loaded" in str(exc.value)
    api_client.close()
    assert api_client._async_client.session is None


def test_chat_completion_connection_error(api_client):
    messages = [{"role": "user", "content": "hi"}]
    async_mock = AsyncMock(side_effect=APIError("Could not connect"))
    with patch.object(api_client._async_client, "chat_completion", async_mock):
        with pytest.raises(APIError) as exc:
            api_client.chat_completion(messages)
    assert "Could not connect" in str(exc.value)
    api_client.close()
    assert api_client._async_client.session is None


def test_circuit_breaker_blocks_calls():
    breaker = CircuitBreaker(fail_max=2, reset_timeout=1)
    client = APIClient(
        base_url="http://test",
        api_key="key",
        model="model",
        circuit_breaker=breaker,
    )
    messages = [{"role": "user", "content": "hi"}]
    with client:

        async def fail(*args, **kwargs):
            breaker.after_call(False)
            raise APIError("fail")

        async_mock = AsyncMock(side_effect=fail)
        with patch.object(client._async_client, "chat_completion", async_mock):
            with pytest.raises(APIError):
                client.chat_completion(messages)
            with pytest.raises(APIError):
                client.chat_completion(messages)
        assert breaker.state == CircuitBreaker.OPEN

        async_mock = AsyncMock(
            return_value={"choices": [{"message": {"content": "ok"}}]}
        )
        with patch.object(client._async_client, "chat_completion", async_mock) as call:
            with pytest.raises(APIError):
                client.chat_completion(messages)
            call.assert_not_awaited()

        time.sleep(1.1)

        async def success(*args, **kwargs):
            breaker.after_call(True)
            return {"choices": [{"message": {"content": "ok"}}]}

        async_mock = AsyncMock(side_effect=success)
        with patch.object(client._async_client, "chat_completion", async_mock):
            client.chat_completion(messages)
            async_mock.assert_awaited_once()
        assert breaker.state == CircuitBreaker.CLOSED
