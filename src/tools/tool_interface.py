from __future__ import annotations

from typing import Protocol, Dict, Any


class ToolInterface(Protocol):
    """Interface for tool implementations."""

    def can_handle(self, command: str) -> bool:
        """Return True if this tool can handle the given command."""
        ...

    def execute(self, command: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute the command and return a result dictionary."""
        ...

