from collections import defaultdict
from typing import Callable, Dict, List, Any

from .logging_config import get_logger

class EventManager:
    """Simple observer pattern implementation."""

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable[..., None]]] = defaultdict(list)
        self.logger = get_logger(f"{__name__}.EventManager")

    def subscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Subscribe to an event."""
        self._listeners[event].append(callback)
        self.logger.debug("Subscribed to event", event=event, listener=callback.__name__)

    def unsubscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Unsubscribe from an event."""
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)
            self.logger.debug("Unsubscribed from event", event=event, listener=callback.__name__)

    def emit(self, event: str, **data: Any) -> None:
        """Emit an event to all listeners."""
        listeners = list(self._listeners.get(event, []))
        self.logger.debug("Emitting event", event=event, listeners=len(listeners))
        for callback in listeners:
            try:
                callback(**data)
            except Exception as exc:
                self.logger.error("Event handler error", event=event, error=str(exc))
