from unittest.mock import Mock, patch
import requests

import pytest

from src.core.api_client import APIClient, APIError


def _create_client():
    return APIClient(base_url="http://test", api_key="key", model="model")


def test_chat_completion_success():
    client = _create_client()
    messages = [{"role": "user", "content": "hi"}]
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "hello"}}]
    }
    mock_response.raise_for_status = Mock()
    with patch.object(client.session, "post", return_value=mock_response) as post:
        response = client.chat_completion(messages)
        post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
    assert response["choices"][0]["message"]["content"] == "hello"
    assert client.extract_content(response) == "hello"


def test_chat_completion_model_not_loaded():
    client = _create_client()
    messages = [{"role": "user", "content": "hi"}]
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"message": "Engine is not loaded"}
    http_error = requests.exceptions.HTTPError(response=mock_response)
    mock_response.raise_for_status.side_effect = http_error
    with patch.object(client.session, "post", return_value=mock_response):
        with pytest.raises(APIError) as exc:
            client.chat_completion(messages)
    assert "Model is not loaded" in str(exc.value)


def test_chat_completion_connection_error():
    client = _create_client()
    messages = [{"role": "user", "content": "hi"}]
    with patch.object(
        client.session, "post", side_effect=requests.exceptions.ConnectionError
    ):
        with pytest.raises(APIError) as exc:
            client.chat_completion(messages)
    assert "Could not connect" in str(exc.value)
