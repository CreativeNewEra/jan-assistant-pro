from __future__ import annotations

import os
from typing import Any, List, Optional


class Command:
    """Abstract command with execute and undo."""

    def execute(self) -> Any:
        raise NotImplementedError

    def undo(self) -> Any:
        raise NotImplementedError


class UndoRedoManager:
    """Simple undo/redo stack manager."""

    def __init__(self) -> None:
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    def execute(self, command: Command) -> Any:
        result = command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()
        return result

    def undo_last(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return True

    def redo_last(self) -> bool:
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        return True


class FileWriteCommand(Command):
    """Command for writing a file with undo support."""

    def __init__(
        self,
        file_tools: "FileTools",
        path: str,
        content: str,
        *,
        encoding: str = "utf-8",
        overwrite: bool = True,
    ) -> None:
        from src.tools.file_tools import FileTools

        self.file_tools = file_tools
        self.path = path
        self.content = content
        self.encoding = encoding
        self.overwrite = overwrite
        self._prev_exists = os.path.exists(path)
        self._prev_content: Optional[str] = None
        if self._prev_exists:
            try:
                with open(path, "r", encoding=encoding) as f:
                    self._prev_content = f.read()
            except Exception:
                self._prev_content = ""

    def execute(self) -> Any:
        return self.file_tools.write_file(
            self.path, self.content, self.encoding, self.overwrite
        )

    def undo(self) -> Any:
        if self._prev_exists:
            self.file_tools.write_file(
                self.path, self._prev_content or "", self.encoding, overwrite=True
            )
        else:
            if os.path.exists(self.path):
                self.file_tools.delete_file(self.path)


class MemoryRememberCommand(Command):
    """Command for remembering a value with undo support."""

    def __init__(self, memory_manager: "MemoryManager", key: str, value: str, category: str) -> None:
        from src.core.memory import MemoryManager

        self.memory_manager = memory_manager
        self.key = key
        self.value = value
        self.category = category
        self._prev = memory_manager.recall(key)

    def execute(self) -> Any:
        return self.memory_manager.remember(self.key, self.value, self.category)

    def undo(self) -> Any:
        if self._prev:
            self.memory_manager.remember(
                self.key,
                self._prev["value"],
                self._prev.get("category", "general"),
            )
        else:
            self.memory_manager.forget(self.key)


class MemoryForgetCommand(Command):
    """Command for forgetting a value with undo support."""

    def __init__(self, memory_manager: "MemoryManager", key: str) -> None:
        from src.core.memory import MemoryManager

        self.memory_manager = memory_manager
        self.key = key
        self._prev = memory_manager.recall(key)

    def execute(self) -> Any:
        return self.memory_manager.forget(self.key)

    def undo(self) -> Any:
        if self._prev:
            self.memory_manager.remember(
                self.key,
                self._prev["value"],
                self._prev.get("category", "general"),
            )

