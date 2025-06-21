"""Asynchronous API client for Jan Assistant Pro"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp

from .exceptions import APIError
from .cache import DiskCache, LRUCache


class AsyncAPIClient:
    """Async client for interacting with OpenAI-compatible APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 30,
        cache_size: int = 0,
        cache_ttl: float = 60.0,
        disk_cache: Optional[DiskCache] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = LRUCache(cache_size, cache_ttl) if cache_size > 0 else None
        self.disk_cache = disk_cache

    async def __aenter__(self) -> "AsyncAPIClient":
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=100, force_close=False)
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            self.session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
            )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            await self.__aenter__()
        assert self.session is not None
        return self.session

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send an async chat completion request."""
        session = await self._ensure_session()
        url = f"{self.base_url}/chat/completions"

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        cache_key = json.dumps(payload, sort_keys=True)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        if self.disk_cache:
            cached = self.disk_cache.get(cache_key)
            if cached is not None:
                if self.cache:
                    self.cache.set(cache_key, cached)
                return cached

        try:
            async with session.post(url, json=payload, timeout=self.timeout) as resp:
                try:
                    resp.raise_for_status()
                except aiohttp.ClientResponseError:
                    error_detail = ""
                    try:
                        error_json = await resp.json()
                        error_detail = error_json.get("message", "")
                    except Exception:
                        pass

                    if resp.status == 400:
                        if "Engine is not loaded" in error_detail:
                            raise APIError(
                                "Model is not loaded in Jan. Please start your model first."
                            )
                        raise APIError(f"Bad request: {error_detail}")
                    if resp.status == 401:
                        raise APIError("Authentication failed. Check your API key.")
                    if resp.status == 404:
                        raise APIError("API endpoint not found. Check your base URL.")
                    raise APIError(f"HTTP {resp.status}: {error_detail}")

                result = await resp.json()
                if self.cache:
                    self.cache.set(cache_key, result)
                if self.disk_cache:
                    self.disk_cache.set(cache_key, result)
                return result
        except asyncio.TimeoutError as exc:
            raise APIError("Request timed out") from exc
        except aiohttp.ClientError as exc:
            raise APIError("Could not connect to API server. Is Jan running?") from exc
        except Exception as exc:
            raise APIError(f"Unexpected error: {exc}") from exc

    async def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        session = await self._ensure_session()
        url = f"{self.base_url}/models"

        try:
            async with session.get(url, timeout=self.timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
        except asyncio.TimeoutError as exc:
            raise APIError("Request timed out") from exc
        except aiohttp.ClientError as exc:
            raise APIError("Failed to get models: network error") from exc
        except Exception as exc:
            raise APIError(f"Failed to get models: {exc}") from exc

    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            await self.chat_completion([{"role": "user", "content": "hi"}])
            return True
        except APIError:
            return False
        except Exception:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status information."""
        status = {
            "connected": False,
            "model_loaded": False,
            "latency_ms": None,
            "error": None,
        }

        try:
            start = asyncio.get_event_loop().time()
            response = await self.chat_completion([{"role": "user", "content": "ping"}])
            end = asyncio.get_event_loop().time()
            status["latency_ms"] = round((end - start) * 1000, 2)
            status["connected"] = True
            status["model_loaded"] = True
        except APIError as exc:
            status["error"] = str(exc)
            if "not loaded" in str(exc).lower():
                status["connected"] = True
        except Exception as exc:
            status["error"] = f"Connection failed: {exc}"
        return status

    @staticmethod
    def extract_content(response: Dict[str, Any]) -> str:
        """Extract text content from chat completion response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise APIError("Invalid response format: missing content") from exc

    @staticmethod
    def extract_reasoning(response: Dict[str, Any]) -> Optional[str]:
        """Extract reasoning content if available."""
        try:
            return response["choices"][0]["message"].get("reasoning_content")
        except (KeyError, IndexError):
            return None

    @staticmethod
    def get_usage_stats(response: Dict[str, Any]) -> Dict[str, int]:
        """Extract usage statistics from response."""
        usage = response.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
