import types
from pathlib import Path

from src.plugins.plugin_loader import PluginLoader
from src.tools.tool_registry import ToolRegistry


def test_plugin_loader(tmp_path):
    plugin_code = '''from src.tools.base_tool import BaseTool, ToolInfo

class HelloTool(BaseTool):
    def get_tool_info(self):
        return ToolInfo(name="hello", description="say", category="test", parameters=[])
    def execute(self, **kwargs):
        return self._create_success_response("hi")
'''
    plugin_file = tmp_path / "my_plugin.py"
    plugin_file.write_text(plugin_code)

    registry = ToolRegistry()
    loader = PluginLoader(registry)
    count = loader.load_plugins(str(tmp_path))

    assert count == 1
    result = registry.execute_tool("hello")
    assert result["success"] is True
    assert result["result"] == "hi"
