import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import tkinter as tk
from gui.enhanced_widgets import ChatInput, StatusBar


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


class TestStatusBar(unittest.TestCase):
    def test_connection_indicator(self):
        root = create_root_or_skip()
        bar = StatusBar(root)
        bar.set_connected(True)
        self.assertEqual(bar.indicator.cget("fg"), "#00ff00")
        bar.set_connected(False)
        self.assertEqual(bar.indicator.cget("fg"), "#ff0000")
        root.destroy()


if __name__ == "__main__":
    unittest.main()
