from unittest.mock import AsyncMock, patch

import pytest


from src.core.api_client import APIClient, APIError


def _create_client():
    return APIClient(base_url="http://test", api_key="key", model="model")


def test_chat_completion_success():
    messages = [{"role": "user", "content": "hi"}]
    async_mock = AsyncMock(return_value={"choices": [{"message": {"content": "hello"}}]})
    with _create_client() as client:
        with patch.object(client._async_client, "chat_completion", async_mock):
            response = client.chat_completion(messages)
            async_mock.assert_awaited_once_with(
                messages, stream=False, temperature=0.7, max_tokens=None
            )
        assert response["choices"][0]["message"]["content"] == "hello"
        assert client.extract_content(response) == "hello"
    assert client._async_client.session is None


def test_chat_completion_model_not_loaded():
    messages = [{"role": "user", "content": "hi"}]
    async_mock = AsyncMock(side_effect=APIError("Model is not loaded"))
    with _create_client() as client:
        with patch.object(client._async_client, "chat_completion", async_mock):
            with pytest.raises(APIError) as exc:
                client.chat_completion(messages)
        assert "Model is not loaded" in str(exc.value)
    assert client._async_client.session is None


def test_chat_completion_connection_error():
    messages = [{"role": "user", "content": "hi"}]
    async_mock = AsyncMock(side_effect=APIError("Could not connect"))
    with _create_client() as client:
        with patch.object(client._async_client, "chat_completion", async_mock):
            with pytest.raises(APIError) as exc:
                client.chat_completion(messages)
        assert "Could not connect" in str(exc.value)
    assert client._async_client.session is None
