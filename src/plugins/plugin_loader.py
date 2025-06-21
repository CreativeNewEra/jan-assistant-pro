from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Optional

from src.core.event_manager import EventManager
from src.tools.tool_registry import ToolRegistry


class PluginLoader:
    """Load tool plugins from a directory."""

    def __init__(self, registry: ToolRegistry, event_manager: Optional[EventManager] = None) -> None:
        self.registry = registry
        self.event_manager = event_manager

    def load_plugins(self, plugin_dir: str) -> int:
        """Load all plugin modules in a directory."""
        path = Path(plugin_dir)
        if not path.exists():
            return 0
        count = 0
        for plugin_file in path.glob("*.py"):
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                count += self.registry.auto_discover_tools(module_name)
                if self.event_manager:
                    self.event_manager.emit("plugin_loaded", name=module_name, path=str(plugin_file))
        return count
