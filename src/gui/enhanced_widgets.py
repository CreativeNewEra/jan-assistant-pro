"""GUI widget enhancements for Jan Assistant Pro."""

import tkinter as tk
from datetime import datetime
from tkinter import ttk


class StatusBar(tk.Frame):
    """A status bar with connection indicator and optional progress."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        bg = kwargs.get(
            "bg", master["bg"] if isinstance(master, tk.Widget) else "white"
        )
        self.configure(bg=bg)

        # Using U+25CF (BLACK CIRCLE) to represent the connection indicator.
        self.indicator = tk.Label(self, text="\u25CF", fg="#ff0000", bg=bg)
        self.indicator.pack(side=tk.LEFT, padx=(0, 5))

        self.label = tk.Label(self, text="Ready", anchor="w", fg="#00ff00", bg=bg)
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=80)
        self.progress_running = False

    def set_status(
        self,
        text: str,
        color: str = "#00ff00",
        progress: bool | tuple[int, int] = False,
    ) -> None:
        """Update the status text and optionally show progress.

        The ``progress`` argument accepts either ``True``/``False`` to toggle an
        indeterminate progress bar, or a ``(value, maximum)`` tuple to show
        determinate progress.
        """

        self.label.config(text=text, fg=color)

        if progress is True:
            if not self.progress_running or self.progress["mode"] != "indeterminate":
                self.progress.config(mode="indeterminate")
                self.progress.pack(side=tk.RIGHT, padx=5)
                self.progress.start()
                self.progress_running = True
        elif isinstance(progress, tuple):
            value, maximum = progress
            if not self.progress_running or self.progress["mode"] != "determinate":
                self.progress.config(mode="determinate", maximum=maximum)
                self.progress.pack(side=tk.RIGHT, padx=5)
                self.progress_running = True
            self.progress["value"] = value
            if value >= maximum:
                self.progress.pack_forget()
                self.progress_running = False
        else:
            if self.progress_running:
                self.progress.stop()
                self.progress.pack_forget()
                self.progress_running = False

        self.update_idletasks()

    def set_connected(self, connected: bool) -> None:
        """Display connection state using the indicator color."""
        self.indicator.config(fg="#00ff00" if connected else "#ff0000")
        self.update_idletasks()


class ChatInput(tk.Entry):
    """Entry widget with history navigation and send callback."""

    def __init__(self, master, send_callback=None, history_limit: int = 50, **kwargs):
        super().__init__(master, **kwargs)
        self.send_callback = send_callback
        self.history_limit = history_limit
        self.history = []
        self.history_index = None

        self.shortcut_manager = ShortcutManager(self)
        self.shortcut_manager.register("<Return>", self._on_submit)
        self.shortcut_manager.register("<Up>", self._on_up)
        self.shortcut_manager.register("<Down>", self._on_down)
        self.shortcut_manager.register("<Control-s>", self._on_save)
        self.shortcut_manager.register("<Control-m>", self._on_memory)
        self.shortcut_manager.register("<Control-z>", self._on_undo)
        self.shortcut_manager.register("<Control-y>", self._on_redo)
        self.shortcut_manager.register("<F1>", self._on_help)

    def _on_submit(self, event=None):
        text = self.get().strip()
        if not text:
            return "break"
        self.history.append(text)
        if len(self.history) > self.history_limit:
            self.history.pop(0)
        self.history_index = None
        self.delete(0, tk.END)
        if self.send_callback:
            self.send_callback(text)
        return "break"

    def _on_up(self, event=None):
        if not self.history:
            return "break"
        if self.history_index is None:
            self.history_index = len(self.history) - 1
        else:
            self.history_index = max(0, self.history_index - 1)
        self._show_history()
        return "break"

    def _on_down(self, event=None):
        if self.history_index is None:
            return "break"
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self._show_history()
        else:
            self.history_index = None
            self.delete(0, tk.END)
        return "break"

    def _show_history(self):
        self.delete(0, tk.END)
        if self.history_index is not None:
            self.insert(0, self.history[self.history_index])

    def submit(self):
        """Public method to trigger the send callback."""
        self._on_submit()

    # ------------------------------------------------------------------
    # Shortcut event handlers
    # ------------------------------------------------------------------

    def _trigger(self, event_name: str):
        """Generate a virtual event for the bound action."""
        self.event_generate(event_name)
        return "break"

    def _on_save(self, event=None):
        return self._trigger("<<SaveChat>>")

    def _on_memory(self, event=None):
        return self._trigger("<<ViewMemory>>")

    def _on_undo(self, event=None):
        return self._trigger("<<UndoAction>>")

    def _on_redo(self, event=None):
        return self._trigger("<<RedoAction>>")

    def _on_help(self, event=None):
        return self._trigger("<<ShowHelp>>")


class EnhancedChatDisplay(tk.Text):
    """Text widget specialized for chat conversations."""

    def __init__(self, master, **kwargs):
        super().__init__(master, wrap=tk.WORD, state=tk.DISABLED, **kwargs)
        self.tag_config("user", foreground="#00ff00")
        self.tag_config("assistant", foreground="#87CEEB")
        self.tag_config("tool", foreground="#FFA500")
        self.tag_config("error", foreground="#ff6b6b")
        self.tag_config("system", foreground=kwargs.get("fg", "black"))

    def add_message(self, sender: str, message: str) -> None:
        """Append a message to the display with timestamp and styling."""
        self.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        if sender == "You":
            tag = "user"
        elif sender == "🤖 Assistant":
            tag = "assistant"
        elif sender == "🔧 Tool":
            tag = "tool"
        elif sender == "⚠️ Error":
            tag = "error"
        else:
            tag = "system"
        self.insert(tk.END, f"[{timestamp}] {sender}:\n{message}\n\n", tag)
        self.config(state=tk.DISABLED)
        self.see(tk.END)
