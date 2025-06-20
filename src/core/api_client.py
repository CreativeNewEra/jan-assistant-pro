"""
API client for communicating with Jan.ai and other OpenAI-compatible APIs
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import httpx


class AsyncAPIClient:
    """Asynchronous client for interacting with OpenAI-compatible APIs."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None

    def _create_session(self) -> httpx.AsyncClient:
        client = httpx.AsyncClient(timeout=self.timeout)
        client.headers.update(
            {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        )
        return client

    async def __aenter__(self) -> "AsyncAPIClient":
        if self.session is None or self.session.is_closed:
            self.session = self._create_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.session and not self.session.is_closed:
            await self.session.aclose()
        self.session = None

    async def _ensure_session(self) -> httpx.AsyncClient:
        if self.session is None or self.session.is_closed:
            self.session = self._create_session()
        return self.session

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        session = await self._ensure_session()
        try:
            response = await session.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            raise APIError("Request timed out")
        except httpx.RequestError:
            raise APIError("Could not connect to API server. Is Jan running?")
        except httpx.HTTPStatusError as e:
            response = e.response
            if response.status_code == 400:
                error_detail = response.json().get("message", "Unknown error")
                if "Engine is not loaded" in error_detail:
                    raise APIError("Model is not loaded in Jan. Please start your model first.")
                else:
                    raise APIError(f"Bad request: {error_detail}")
            elif response.status_code == 401:
                raise APIError("Authentication failed. Check your API key.")
            elif response.status_code == 404:
                raise APIError("API endpoint not found. Check your base URL.")
            else:
                raise APIError(f"HTTP {response.status_code}: {response.text}")
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response from server")
        except Exception as e:  # pragma: no cover - unexpected branch
            raise APIError(f"Unexpected error: {str(e)}")

    async def get_models(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/models"

        session = await self._ensure_session()
        try:
            response = await session.get(url)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            raise APIError(f"Failed to get models: {str(e)}")

    async def health_check(self) -> bool:
        try:
            test_messages = [{"role": "user", "content": "hi"}]
            await self.chat_completion(test_messages)
            return True
        except APIError:
            return False
        except Exception:
            return False

    async def test_connection(self) -> Dict[str, Any]:
        status = {
            "connected": False,
            "model_loaded": False,
            "latency_ms": None,
            "error": None,
        }

        try:
            start_time = time.time()

            test_messages = [{"role": "user", "content": "ping"}]
            await self.chat_completion(test_messages)

            end_time = time.time()
            status["latency_ms"] = round((end_time - start_time) * 1000, 2)
            status["connected"] = True
            status["model_loaded"] = True

        except APIError as e:
            status["error"] = str(e)
            if "not loaded" in str(e).lower():
                status["connected"] = True

        except Exception as e:
            status["error"] = f"Connection failed: {str(e)}"

        return status

    async def close(self) -> None:
        if self.session and not self.session.is_closed:
            await self.session.aclose()
        self.session = None


class APIClient:
    """Synchronous wrapper around :class:`AsyncAPIClient`."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

        self._async_client = AsyncAPIClient(
            base_url=base_url, api_key=api_key, model=model, timeout=timeout
        )

    def __enter__(self) -> "APIClient":
        self._run(self._async_client.__aenter__())
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._run(self._async_client.__aexit__(exc_type, exc, tb))

    def _run(self, coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)

    def close(self) -> None:
        """Close the underlying asynchronous client."""
        self._run(self._async_client.close())
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synchronously send a chat completion request."""

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
            return response['choices'][0]['message']['content']
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
            return response['choices'][0]['message'].get('reasoning_content')
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
            usage = response.get('usage', {})
            return {
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0)
            }
        except Exception:
            return {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass
