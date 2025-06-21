from __future__ import annotations

from typing import Dict

from .cache import LRUCache
from .logging_config import get_logger

"""Handler for offline or degraded mode operations."""


class DegradedModeHandler:
    """Provide responses when the application is offline."""

    def __init__(self) -> None:
        self.offline_responses: Dict[str, str] = {
            "greeting": "Hello! I'm currently offline but can help with cached responses.",
            "help": "Available offline commands: ...",
        }
        self.last_successful_responses: LRUCache[str, str] = LRUCache(maxsize=100)
        self.logger = get_logger(f"{__name__}.DegradedModeHandler")

    def cache_response(self, prompt: str, response: str) -> None:
        """Store a successful response for offline use."""
        self.last_successful_responses[prompt] = response
        self.logger.debug("Cached successful response", prompt=prompt, cached=response)

    def _classify_intent(self, message: str) -> str:
        """Return a simple intent label based on the message."""
        lowered = message.lower()
        if "help" in lowered:
            return "help"
        if any(word in lowered for word in ("hello", "hi", "hey")):
            return "greeting"
        return "unknown"

    def handle_offline_request(self, message: str) -> str:
        """Return an offline response based on cached data or intent."""
        if cached := self.last_successful_responses.get(message):
            return f"\U0001f4f5 Offline Mode - Last response:\n{cached}"

        return self.offline_responses.get(
            self._classify_intent(message),
            "\U0001f4f5 I'm currently offline. Please check your connection.",
        )


__all__ = ["DegradedModeHandler"]
