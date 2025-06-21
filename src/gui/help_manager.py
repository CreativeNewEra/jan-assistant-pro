from __future__ import annotations

from tkinter import Widget, messagebox
from typing import Optional

from src.gui.enhanced_widgets import ChatInput
from src.tools.tool_registry import ToolRegistry, get_registry


class HelpManager:
    """Provide contextual help using tool metadata."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        chat_input: Optional[ChatInput] = None,
    ) -> None:
        self.registry = registry or get_registry()
        self.chat_input = chat_input

    # ------------------------------------------------------------------
    def get_tool_help(self, tool_name: Optional[str] = None) -> str:
        """Return help text for a specific tool or all tools."""
        return self.registry.generate_help(tool_name)

    def get_context_help(self, widget: Optional[Widget] = None) -> str:
        """Return help text based on the focused widget."""
        if widget is None and self.chat_input is not None:
            widget = self.chat_input.master.focus_get()

        help_text = self.get_tool_help()
        if widget is self.chat_input and self.chat_input.history:
            last = self.chat_input.history[-1]
            help_text = f"Last command: {last}\n\n" + help_text
        return help_text

    def show_help(self, widget: Optional[Widget] = None) -> None:
        """Display contextual help in a message box."""
        messagebox.showinfo("Help", self.get_context_help(widget))
