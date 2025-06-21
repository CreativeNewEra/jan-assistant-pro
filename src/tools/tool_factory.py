from importlib import import_module
from typing import Any, Dict

from .base_tool import BaseTool
from .tool_registry import ToolRegistry, ToolRegistryError


class ToolFactory:
    """Factory for creating tools dynamically."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def create_tool(self, module_path: str, class_name: str, config: Dict[str, Any] | None = None) -> BaseTool:
        module = import_module(module_path)
        cls = getattr(module, class_name)
        if not issubclass(cls, BaseTool):
            raise ToolRegistryError(f"{class_name} must inherit from BaseTool")
        self.registry.register_tool(cls, config)
        return self.registry.get_tool(cls.__name__)
