import os
import sys
import unittest

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
from src.gui.enhanced_widgets import (
    ChatInput,
    EnhancedChatDisplay,
    StatusBar,
)

tk = pytest.importorskip("tkinter", reason="required for GUI widget tests")


def create_root_or_skip():
    try:
        root = tk.Tk()
        root.withdraw()
        return root
    except tk.TclError:
        raise unittest.SkipTest("Tkinter not available")


class TestChatInput(unittest.TestCase):
    def test_history_navigation(self):
        root = create_root_or_skip()
        messages = []
        input_widget = ChatInput(root, send_callback=messages.append)
        # submit first message
        input_widget.insert(0, "first")
        input_widget.submit()
        input_widget.insert(0, "second")
        input_widget.submit()

        input_widget._on_up()
        self.assertEqual(input_widget.get(), "second")
        input_widget._on_up()
        self.assertEqual(input_widget.get(), "first")
        input_widget._on_down()
        self.assertEqual(input_widget.get(), "second")
        root.destroy()

    def test_shortcut_events(self):
        root = create_root_or_skip()
        events = []
        root.bind("<<SaveChat>>", lambda e: events.append("save"))
        root.bind("<<ViewMemory>>", lambda e: events.append("memory"))
        root.bind("<<UndoAction>>", lambda e: events.append("undo"))
        root.bind("<<RedoAction>>", lambda e: events.append("redo"))
        root.bind("<<ShowHelp>>", lambda e: events.append("help"))

        input_widget = ChatInput(root)

        input_widget._on_save()
        input_widget._on_memory()
        input_widget._on_undo()
        input_widget._on_redo()
        input_widget._on_help()

        self.assertEqual(events, ["save", "memory", "undo", "redo", "help"])
        root.destroy()

    def test_drop_populates_command(self):
        root = create_root_or_skip()
        input_widget = ChatInput(root)

        class Event:
            def __init__(self, data):
                self.data = data

        input_widget._on_drop(Event("/tmp/test.txt"))
        self.assertEqual(input_widget.get(), "TOOL_READ_FILE: /tmp/test.txt")
        root.destroy()


class TestEnhancedChatDisplay(unittest.TestCase):
    def test_drop_calls_callback(self):
        root = create_root_or_skip()
        called = []

        def cb(paths):
            called.append(paths)

        display = EnhancedChatDisplay(root, drop_callback=cb)

        class Event:
            def __init__(self, data):
                self.data = data

        display._on_drop(Event("/tmp/foo.txt"))
        self.assertEqual(called, [["/tmp/foo.txt"]])
        root.destroy()


class TestStatusBar(unittest.TestCase):
    def test_connection_indicator(self):
        root = create_root_or_skip()
        bar = StatusBar(root)
        bar.set_connected(True)
        self.assertEqual(bar.indicator.cget("fg"), "#00ff00")
        bar.set_connected(False)
        self.assertEqual(bar.indicator.cget("fg"), "#ff0000")
        root.destroy()

    def test_determinate_progress(self):
        root = create_root_or_skip()
        bar = StatusBar(root)
        bar.set_status("Working", progress=(1, 2))
        self.assertEqual(bar.progress["mode"], "determinate")
        self.assertEqual(bar.progress["value"], 1)
        bar.set_status("Done", progress=(2, 2))
        self.assertFalse(bar.progress.winfo_ismapped())
        root.destroy()


if __name__ == "__main__":
    unittest.main()
