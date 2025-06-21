"""
Main GUI window for Jan Assistant Pro
Refactored from the original working implementation
"""

import threading
import tkinter as tk
from concurrent.futures import Future, ThreadPoolExecutor
from tkinter import filedialog, messagebox
from typing import Any, Dict

from src.core.app_controller import AppController
from src.core.config import Config
from src.core.logging_config import get_logger
from src.gui.enhanced_widgets import ChatInput, EnhancedChatDisplay, StatusBar
from src.gui.help_manager import HelpManager


class JanAssistantGUI:
    """Main GUI application for Jan Assistant Pro"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"theme": self.config.theme},
        )
        self.controller = AppController(config)

        # Setup GUI
        self.setup_gui()

        # Thread pool executor for async processing
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title("🤖 Jan Assistant Pro")
        self.root.geometry(self.config.window_size)

        # Menu
        menu_bar = tk.Menu(self.root)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(
            label="Show Help", accelerator="F1", command=self.show_help
        )
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu_bar)
        # Keyboard shortcuts
        # Map direct keyboard shortcuts to virtual events
        shortcut_to_event = {
            "<Control-s>": "<<SaveChat>>",
            "<Control-m>": "<<ViewMemory>>",
            "<Control-z>": "<<UndoAction>>",
            "<Control-y>": "<<RedoAction>>",
            "<F1>": "<<ShowHelp>>",
        }
        for shortcut, event in shortcut_to_event.items():
            self.root.bind(
                shortcut, lambda e, event=event: self.root.event_generate(event)
            )

        # Bind virtual events to action methods
        self.root.bind("<<SaveChat>>", lambda e: self.save_chat())
        self.root.bind("<<ViewMemory>>", lambda e: self.view_memory())
        self.root.bind("<<UndoAction>>", lambda e: self.undo_action())
        self.root.bind("<<RedoAction>>", lambda e: self.redo_action())
        self.root.bind("<<ShowHelp>>", lambda e: self.show_help())

        # Apply theme
        if self.config.theme == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🤖 Jan Assistant Pro",
            font=("Arial", 16, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        )
        title_label.pack(pady=(0, 10))

        # Chat display frame with scrollbar
        chat_frame = tk.Frame(main_frame, bg=self.bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Chat display widget
        self.chat_display = EnhancedChatDisplay(
            chat_frame,
            bg=self.chat_bg_color,
            fg=self.fg_color,
            font=(
                self.config.get("ui.font_family", "Consolas"),
                self.config.get("ui.font_size", 10),
            ),
        )

        # Manual scrollbar
        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_display.yview)
        self.chat_display.config(yscrollcommand=scrollbar.set)

        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Input frame
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        # User input
        self.chat_input = ChatInput(
            input_frame,
            send_callback=self.send_message,
            font=("Arial", 12),
            bg=self.input_bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
        )
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Help manager needs reference to chat input
        self.help_manager = HelpManager(chat_input=self.chat_input)

        # Send button
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.chat_input.submit,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
        )
        self.send_button.pack(side=tk.RIGHT)

        # Status and buttons frame
        bottom_frame = tk.Frame(main_frame, bg=self.bg_color)
        bottom_frame.pack(fill=tk.X)

        # Status bar
        self.status_bar = StatusBar(bottom_frame, bg=self.bg_color)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Buttons
        self._create_buttons(bottom_frame)

        # Welcome message
        self.add_to_chat("🤖 Assistant", self._get_welcome_message())

        # Test API connection
        self._test_api_connection()

        self.chat_input.focus()

    def _apply_dark_theme(self):
        """Apply dark theme colors"""
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.chat_bg_color = "#1e1e1e"
        self.input_bg_color = "#3c3c3c"
        self.root.configure(bg=self.bg_color)

    def _apply_light_theme(self):
        """Apply light theme colors"""
        self.bg_color = "#ffffff"
        self.fg_color = "#000000"
        self.chat_bg_color = "#f5f5f5"
        self.input_bg_color = "#ffffff"
        self.root.configure(bg=self.bg_color)

    def _create_buttons(self, parent):
        """Create action buttons"""
        buttons_frame = tk.Frame(parent, bg=self.bg_color)
        buttons_frame.pack(side=tk.RIGHT)

        buttons = [
            ("💾 Save", self.save_chat, "#FF9800"),
            ("🧠 Memory", self.view_memory, "#9C27B0"),
            ("⚙️ Settings", self.show_settings, "#607D8B"),
            ("🔧 Test API", self.test_api, "#2196F3"),
            ("🗑️ Clear", self.clear_chat, "#F44336"),
            ("↩️ Undo", self.undo_action, "#795548"),
            ("↪️ Redo", self.redo_action, "#009688"),
            ("❓ Help", self.show_help, "#3F51B5"),
        ]

        for text, command, color in buttons:
            tk.Button(
                buttons_frame,
                text=text,
                command=command,
                bg=color,
                fg="white",
                font=("Arial", 9),
            ).pack(side=tk.LEFT, padx=2)

    def _get_welcome_message(self) -> str:
        """Get welcome message"""
        return self.controller.get_welcome_message()

    def _test_api_connection(self):
        """Test API connection on startup"""

        def test():
            status = self.controller.test_api_connection()
            if status["connected"]:
                self.root.after(0, lambda: self.status_bar.set_connected(True))
                self.root.after(
                    0,
                    lambda: self.update_status(
                        "✅ Connected", "#00ff00", progress=False
                    ),
                )
            else:
                error_msg = status.get("error", "Unknown error")
                self.root.after(0, lambda: self.status_bar.set_connected(False))
                self.root.after(
                    0,
                    lambda: self.update_status(
                        f"❌ {error_msg}", "#ff0000", progress=False
                    ),
                )

        threading.Thread(target=test, daemon=True).start()

    def add_to_chat(self, sender: str, message: str):
        """Add message to chat display"""
        self.chat_display.add_message(sender, message)

    def update_status(
        self, status: str, color: str = "#00ff00", progress: bool = False
    ):
        """Update status bar"""
        self.status_bar.set_status(status, color, progress)

    def _handle_future_result(self, future: Future) -> None:
        """Handle results from worker threads."""
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover - safety net
            self.logger.error(
                "Worker thread failed",
                exc_info=True,
                extra={"extra_fields": {"error": str(exc)}},
            )
            error_msg = str(exc)
            self.root.after(0, lambda: self.add_to_chat("⚠️ Error", error_msg))
            self.root.after(
                0, lambda: self.update_status("Ready", "#ff0000", progress=False)
            )
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
            return

        def gui_update() -> None:
            if result.get("type") == "error":
                self.add_to_chat("⚠️ Error", result.get("content", ""))
            else:
                self.add_to_chat("🤖 Assistant", result.get("content", ""))
            self.update_status("Ready", "#00ff00", progress=False)
            self.send_button.config(state=tk.NORMAL)

        self.root.after(0, gui_update)

    def send_message(self, message: str):
        """Send message to assistant"""
        message = message.strip()
        if not message:
            return

        self.add_to_chat("You", message)

        self.send_button.config(state=tk.DISABLED)
        self.update_status("🤔 Thinking...", "#ffff00", progress=True)

        future = self.executor.submit(self.process_message, message)
        future.add_done_callback(self._handle_future_result)

    def process_message(self, message: str) -> Dict[str, Any]:
        """Process message with the controller"""
        try:
            return self.controller.process_message(message)
        except Exception as e:
            return {"type": "error", "content": str(e)}

    # GUI Event handlers
    def save_chat(self):
        """Save chat history"""
        filename = filedialog.asksaveasfilename(
            title="Save chat history",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            try:
                content = self.chat_display.get(1.0, tk.END)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Chat saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def view_memory(self):
        """Show memory contents"""
        memory_window = tk.Toplevel(self.root)
        memory_window.title("🧠 Memory Manager")
        memory_window.geometry("600x400")
        memory_window.configure(bg=self.bg_color)

        # Create notebook-style tabs
        notebook_frame = tk.Frame(memory_window, bg=self.bg_color)
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Memory content
        text_widget = tk.Text(
            notebook_frame,
            bg=self.chat_bg_color,
            fg=self.fg_color,
            font=("Consolas", 10),
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Load memories
        memories = self.controller.memory_manager.list_memories()
        if memories:
            for key, memory in memories:
                text_widget.insert(tk.END, f"🔑 {key}\n")
                text_widget.insert(tk.END, f"   📝 {memory['value']}\n")
                text_widget.insert(
                    tk.END, f"   📁 Category: {memory.get('category', 'general')}\n"
                )
                text_widget.insert(tk.END, f"   📅 {memory['timestamp']}\n\n")
        else:
            text_widget.insert(tk.END, "No memories stored yet.")

        text_widget.config(state=tk.DISABLED)

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg=self.bg_color)

        # Settings content
        tk.Label(
            settings_window,
            text="⚙️ Settings",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(pady=10)

        # API settings
        api_frame = tk.LabelFrame(
            settings_window,
            text="API Configuration",
            bg=self.bg_color,
            fg=self.fg_color,
        )
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            api_frame,
            text=f"URL: {self.controller.config.api_base_url}",
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(anchor=tk.W)
        tk.Label(
            api_frame,
            text=f"Model: {self.controller.config.model_name}",
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(anchor=tk.W)

        # Memory settings
        memory_frame = tk.LabelFrame(
            settings_window, text="Memory", bg=self.bg_color, fg=self.fg_color
        )
        memory_frame.pack(fill=tk.X, padx=10, pady=5)

        stats = self.controller.memory_manager.get_stats()
        tk.Label(
            memory_frame,
            text=f"Total memories: {stats['total_entries']}",
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(anchor=tk.W)
        tk.Label(
            memory_frame,
            text=f"Categories: {', '.join(stats['categories'])}",
            bg=self.bg_color,
            fg=self.fg_color,
        ).pack(anchor=tk.W)

    def show_help(self):
        """Display contextual help."""
        widget = self.root.focus_get()
        self.help_manager.show_help(widget)

    def test_api(self):
        """Test API connection"""

        def test():
            self.root.after(
                0,
                lambda: self.update_status(
                    "🔄 Testing API...", "#ffff00", progress=True
                ),
            )
            status = self.controller.test_api_connection()

            if status["connected"]:
                msg = f"✅ Connected! Latency: {status.get('latency_ms', 'N/A')}ms"
                self.root.after(
                    0, lambda: self.update_status(msg, "#00ff00", progress=False)
                )
                self.root.after(
                    0, lambda: self.add_to_chat("System", f"API test successful. {msg}")
                )
                self.root.after(0, lambda: self.status_bar.set_connected(True))
            else:
                error = status.get("error", "Unknown error")
                self.root.after(
                    0,
                    lambda: self.update_status("❌ Failed", "#ff0000", progress=False),
                )
                self.root.after(
                    0, lambda: self.add_to_chat("System", f"API test failed: {error}")
                )
                self.root.after(0, lambda: self.status_bar.set_connected(False))

        threading.Thread(target=test, daemon=True).start()

    def clear_chat(self):
        """Clear chat"""
        if messagebox.askyesno("Clear Chat", "Clear chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.controller.conversation_history = []
            self.add_to_chat("🤖 Assistant", "Chat cleared! How can I help?")

    def undo_action(self):
        """Undo last operation and show result."""
        if self.controller.undo_last():
            self.add_to_chat("System", "Undone")
        else:
            self.add_to_chat("System", "Nothing to undo")

    def redo_action(self):
        """Redo last undone operation and show result."""
        if self.controller.redo_last():
            self.add_to_chat("System", "Redone")
        else:
            self.add_to_chat("System", "Nothing to redo")

    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted")
        finally:
            self.on_close()

    def on_close(self) -> None:
        """Handle application shutdown."""
        try:
            self.controller.memory_manager.save_memory()
        finally:
            self.executor.shutdown(wait=False, cancel_futures=True)
            if self.root.winfo_exists():
                self.root.destroy()
