import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.gui.help_manager import HelpManager
from src.tools.base_tool import BaseTool, ToolInfo, ToolParameter
from src.tools.tool_registry import ToolRegistry


class MockTool(BaseTool):
    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="mock_tool",
            description="Test tool",
            category="testing",
            parameters=[ToolParameter("text", "Some text", str)],
        )

    def execute(self, **kwargs):
        return self._create_success_response("ok")


class TestHelpManager(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register_tool(MockTool)
        self.manager = HelpManager(self.registry)

    def test_get_tool_help(self):
        text = self.manager.get_tool_help("mock_tool")
        self.assertIn("mock_tool", text)
        self.assertIn("Test tool", text)


if __name__ == "__main__":
    unittest.main()
