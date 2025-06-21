from __future__ import annotations

"""Command pattern utilities for Jan Assistant Pro."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol
import logging

from .request_context import RequestContext


@dataclass
class Result:
    """Standard command result."""

    success: bool
    data: Any = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Any = None) -> "Result":
        return cls(True, data, None)

    @classmethod
    def failure(cls, error: str) -> "Result":
        return cls(False, None, error)


@dataclass
class Command:
    """Represents a command to execute."""

    name: str
    params: Dict[str, Any]
    context: Optional[RequestContext] = None


class CommandHandler(Protocol):
    """Handler interface for commands."""

    async def handle(self, command: Command) -> Result:
        ...


class CommandBus:
    """Dispatch commands to registered handlers."""

    def __init__(self) -> None:
        self.handlers: Dict[str, CommandHandler] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, name: str, handler: CommandHandler) -> None:
        self.handlers[name] = handler

    async def execute(self, command: Command) -> Result:
        handler = self.handlers.get(command.name)
        if handler is None:
            return Result.failure(f"Unknown command: {command.name}")
        try:
            return await handler.handle(command)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.exception(
                "Command failed", extra={"command": command.name}
            )
            return Result.failure(str(exc))

