"""
Dynamic tool registry system for Jan Assistant Pro
Manages registration, discovery, and execution of tools
"""

import logging
from typing import Dict, Any, List, Type, Optional, Set
from collections import defaultdict
import inspect

from .base_tool import BaseTool, ToolInfo


class ToolRegistryError(Exception):
    """Custom exception for tool registry errors"""
    pass


class ToolRegistry:
    """
    Central registry for managing tools in the Jan Assistant Pro system.
    
    This registry provides:
    - Dynamic tool registration and discovery
    - Parameter validation
    - Tool categorization
    - Automatic help generation
    - Safe tool execution with error handling
    """
    
    def __init__(self):
        """Initialize the tool registry"""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_info: Dict[str, ToolInfo] = {}
        self._categories: Dict[str, Set[str]] = defaultdict(set)
        self.logger = logging.getLogger("tools.registry")
        
    def register_tool(self, tool_class: Type[BaseTool], 
                     config: Dict[str, Any] = None) -> None:
        """
        Register a tool class with the registry
        
        Args:
            tool_class: Class that inherits from BaseTool
            config: Configuration to pass to the tool instance
            
        Raises:
            ToolRegistryError: If tool registration fails
        """
        try:
            # Validate tool class
            if not issubclass(tool_class, BaseTool):
                raise ToolRegistryError(
                    f"Tool {tool_class.__name__} must inherit from BaseTool"
                )
            
            # Create tool instance
            tool_instance = tool_class(config or {})
            tool_info = tool_instance.get_tool_info()
            
            # Validate tool info
            self._validate_tool_info(tool_info)
            
            # Check for name conflicts
            if tool_info.name in self._tools:
                raise ToolRegistryError(
                    f"Tool '{tool_info.name}' is already registered"
                )
            
            # Register the tool
            self._tools[tool_info.name] = tool_instance
            self._tool_info[tool_info.name] = tool_info
            self._categories[tool_info.category].add(tool_info.name)
            
            self.logger.info(f"Registered tool: {tool_info.name}")
            
        except Exception as e:
            raise ToolRegistryError(
                f"Failed to register tool {tool_class.__name__}: {str(e)}"
            ) from e
    
    def _validate_tool_info(self, tool_info: ToolInfo) -> None:
        """Validate tool information"""
        if not tool_info.name:
            raise ToolRegistryError("Tool name cannot be empty")
        
        if not tool_info.name.isidentifier():
            raise ToolRegistryError(
                f"Tool name '{tool_info.name}' must be a valid identifier"
            )
        
        if not tool_info.description:
            raise ToolRegistryError("Tool description cannot be empty")
        
        if not tool_info.category:
            raise ToolRegistryError("Tool category cannot be empty")
    
    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool from the registry
        
        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self._tools:
            tool_info = self._tool_info[tool_name]
            
            # Remove from registry
            del self._tools[tool_name]
            del self._tool_info[tool_name]
            self._categories[tool_info.category].discard(tool_name)
            
            # Clean up empty categories
            if not self._categories[tool_info.category]:
                del self._categories[tool_info.category]
            
            self.logger.info(f"Unregistered tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool instance by name
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool with given parameters
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool
            
        Returns:
            Tool execution result
        """
        try:
            tool = self.get_tool(tool_name)
            if not tool:
                return {
                    'success': False,
                    'error': f"Tool '{tool_name}' not found",
                    'available_tools': list(self._tools.keys())
                }
            
            # Validate parameters
            is_valid, error_msg = tool.validate_parameters(kwargs)
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Parameter validation failed: {error_msg}",
                    'tool_help': tool.get_usage_help()
                }
            
            # Execute the tool
            result = tool.execute(**kwargs)
            
            # Add execution metadata
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['tool_name'] = tool_name
            result['metadata']['execution_time'] = None  # Could add timing
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                'success': False,
                'error': f"Tool execution failed: {str(e)}",
                'tool_name': tool_name
            }
    
    def list_tools(self, category: str = None) -> List[str]:
        """
        List available tool names
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool names
        """
        if category:
            return list(self._categories.get(category, set()))
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """
        List available tool categories
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """
        Get information about a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            ToolInfo or None if tool not found
        """
        return self._tool_info.get(tool_name)
    
    def get_all_tool_info(self) -> Dict[str, ToolInfo]:
        """
        Get information about all registered tools
        
        Returns:
            Dictionary mapping tool names to ToolInfo
        """
        return self._tool_info.copy()
    
    def generate_help(self, tool_name: str = None) -> str:
        """
        Generate help documentation
        
        Args:
            tool_name: Specific tool name, or None for all tools
            
        Returns:
            Formatted help text
        """
        if tool_name:
            tool = self.get_tool(tool_name)
            if tool:
                return tool.get_usage_help()
            else:
                return f"Tool '{tool_name}' not found.\n\nAvailable tools:\n" + \
                       "\n".join(f"- {name}" for name in sorted(self._tools.keys()))
        
        # Generate help for all tools by category
        help_text = "# Jan Assistant Pro - Available Tools\n\n"
        
        for category in sorted(self._categories.keys()):
            help_text += f"## {category.title()}\n\n"
            
            for tool_name in sorted(self._categories[category]):
                tool = self._tools[tool_name]
                info = self._tool_info[tool_name]
                help_text += f"### {info.name}\n"
                help_text += f"{info.description}\n\n"
                
                if info.examples:
                    help_text += "**Examples:**\n"
                    for example in info.examples:
                        help_text += f"- {example}\n"
                    help_text += "\n"
        
        return help_text
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the registry
        
        Returns:
            Dictionary with registry statistics
        """
        return {
            'total_tools': len(self._tools),
            'categories': dict(self._categories),
            'category_count': len(self._categories),
            'tools_by_category': {
                cat: len(tools) for cat, tools in self._categories.items()
            }
        }
    
    def auto_discover_tools(self, module_path: str) -> int:
        """
        Automatically discover and register tools from a module
        
        Args:
            module_path: Python module path to scan for tools
            
        Returns:
            Number of tools discovered and registered
        """
        try:
            import importlib
            module = importlib.import_module(module_path)
            
            registered_count = 0
            
            for name in dir(module):
                obj = getattr(module, name)
                
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTool) and 
                    obj != BaseTool):
                    
                    try:
                        self.register_tool(obj)
                        registered_count += 1
                    except ToolRegistryError as e:
                        self.logger.warning(
                            f"Could not register {name}: {str(e)}"
                        )
            
            self.logger.info(
                f"Auto-discovered {registered_count} tools from {module_path}"
            )
            return registered_count
            
        except Exception as e:
            self.logger.error(
                f"Error auto-discovering tools from {module_path}: {str(e)}"
            )
            return 0


# Global registry instance
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    return _global_registry


def register_tool(tool_class: Type[BaseTool], 
                 config: Dict[str, Any] = None) -> None:
    """
    Convenience function to register a tool with the global registry
    
    Args:
        tool_class: Tool class to register
        config: Tool configuration
    """
    _global_registry.register_tool(tool_class, config)


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to execute a tool using the global registry
    
    Args:
        tool_name: Name of tool to execute
        **kwargs: Tool parameters
        
    Returns:
        Tool execution result
    """
    return _global_registry.execute_tool(tool_name, **kwargs)
