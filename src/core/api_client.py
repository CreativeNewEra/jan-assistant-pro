"""Synchronous wrapper around the asynchronous :class:`AsyncAPIClient`."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .circuit_breaker import CircuitBreaker
from .exceptions import APIError
from .async_api_client import AsyncAPIClient

class APIClient:
    """Synchronous wrapper around :class:`AsyncAPIClient`."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 30,
        *,
        cache_enabled: bool = False,
        cache_ttl: int = 300,
        cache_size: int = 128,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

        self._async_client = AsyncAPIClient(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout=timeout,
            cache_enabled=cache_enabled,
            cache_ttl=cache_ttl,
            cache_size=cache_size,
            circuit_breaker=circuit_breaker,
        )
        self.breaker = self._async_client.breaker
        self._loop: asyncio.AbstractEventLoop | None = None

    def __enter__(self) -> "APIClient":
        self._run(self._async_client.__aenter__())
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._run(self._async_client.__aexit__(exc_type, exc, tb))

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
            return self._loop

    def _run(self, coro):
        loop = self._ensure_loop()
        return loop.run_until_complete(coro)

    def close(self) -> None:
        """Close the underlying asynchronous client."""
        self._run(self._async_client.close())

    def clear_api_cache(self) -> None:
        """Clear cached API responses."""
        self._async_client.clear_api_cache()

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synchronously send a chat completion request."""
        if self.breaker and not self.breaker.allow():
            raise APIError("Circuit breaker open")

        return self._run(
            self._async_client.chat_completion(
                messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )

    def get_models(self) -> List[Dict[str, Any]]:
        """Synchronously fetch available models."""
        if self.breaker and not self.breaker.allow():
            raise APIError("Circuit breaker open")
        return self._run(self._async_client.get_models())

    def health_check(self) -> bool:
        """Synchronously check API health."""
        return self._run(self._async_client.health_check())

    def test_connection(self) -> Dict[str, Any]:
        """Synchronously test the connection and return status information."""
        return self._run(self._async_client.test_connection())

    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extract the content from a chat completion response

        Args:
            response: The response dictionary from chat_completion

        Returns:
            The text content of the response
        """
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise APIError("Invalid response format: missing content")

    def extract_reasoning(self, response: Dict[str, Any]) -> Optional[str]:
        """
        Extract reasoning content if available (for models that support it)

        Args:
            response: The response dictionary from chat_completion

        Returns:
            The reasoning content or None if not available
        """
        try:
            return response["choices"][0]["message"].get("reasoning_content")
        except (KeyError, IndexError):
            return None

    def get_usage_stats(self, response: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract usage statistics from response

        Args:
            response: The response dictionary from chat_completion

        Returns:
            Dictionary with token usage information
        """
        try:
            usage = response.get("usage", {})
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
        except Exception:
            return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
