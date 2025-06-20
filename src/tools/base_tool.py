"""
Base tool interface for Jan Assistant Pro
Provides the foundation for the dynamic tool registry system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

@dataclass
class ToolParameter:
    """Represents a tool parameter with validation"""
    name: str
    description: str
    param_type: type
    required: bool = True
    default: Any = None
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate parameter value"""
        if self.required and value is None:
            return False, f"Parameter '{self.name}' is required"
        
        if value is not None and not isinstance(value, self.param_type):
            return False, f"Parameter '{self.name}' must be of type {self.param_type.__name__}"
        
        return True, ""

@dataclass
class ToolInfo:
    """Tool metadata and registration information"""
    name: str
    description: str
    category: str
    parameters: List[ToolParameter]
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []

class BaseTool(ABC):
    """
    Abstract base class for all tools in the Jan Assistant Pro system.
    
    This class defines the interface that all tools must implement to be
    compatible with the dynamic tool registry system.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the tool with configuration
        
        Args:
            config: Tool-specific configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"tools.{self.__class__.__name__}")
    
    @abstractmethod
    def get_tool_info(self) -> ToolInfo:
        """
        Return metadata about this tool
        
        Returns:
            ToolInfo: Complete information about the tool's capabilities
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict containing:
            - success: bool indicating if operation succeeded
            - result: Any result data (if success=True)
            - error: str error message (if success=False)
            - metadata: Dict with additional information
        """
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate parameters against tool requirements
        
        Args:
            params: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        tool_info = self.get_tool_info()
        
        for param_info in tool_info.parameters:
            value = params.get(param_info.name)
            is_valid, error = param_info.validate(value)
            if not is_valid:
                return False, error
        
        return True, ""
    
    def _create_success_response(self, result: Any, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Helper to create standardized success response"""
        return {
            'success': True,
            'result': result,
            'metadata': metadata or {}
        }
    
    def _create_error_response(self, error: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Helper to create standardized error response"""
        self.logger.error(f"Tool {self.__class__.__name__} error: {error}")
        return {
            'success': False,
            'error': error,
            'metadata': metadata or {}
        }
    
    def get_usage_help(self) -> str:
        """
        Generate help text for this tool
        
        Returns:
            Formatted help string
        """
        info = self.get_tool_info()
        help_text = f"**{info.name}** - {info.description}\n\n"
        help_text += f"Category: {info.category}\n\n"
        
        if info.parameters:
            help_text += "Parameters:\n"
            for param in info.parameters:
                required_text = "required" if param.required else "optional"
                default_text = f" (default: {param.default})" if param.default is not None else ""
                help_text += f"  - **{param.name}** ({param.param_type.__name__}, {required_text}): {param.description}{default_text}\n"
        
        if info.examples:
            help_text += "\nExamples:\n"
            for example in info.examples:
                help_text += f"  - {example}\n"
        
        return help_text
