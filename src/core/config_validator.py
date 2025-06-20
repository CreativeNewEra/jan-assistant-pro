"""
Configuration validation for Jan Assistant Pro
Provides schema-based validation and type safety for configuration
"""

from typing import Dict, Any, List, Union, Optional, Type
from dataclasses import dataclass, field
import json
import os
from pathlib import Path

from .exceptions import ConfigurationError, ValidationError

@dataclass
class ValidationRule:
    """Represents a validation rule for configuration values"""
    field_type: Type
    required: bool = True
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    validator_func: Optional[callable] = None
    description: str = ""

@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    rules: Dict[str, ValidationRule] = field(default_factory=dict)
    
    def add_rule(self, field_path: str, rule: ValidationRule):
        """Add a validation rule for a field"""
        self.rules[field_path] = rule
    
    def validate(self, config_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate configuration against schema
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        for field_path, rule in self.rules.items():
            try:
                value = self._get_nested_value(config_data, field_path)
                is_valid, error = self._validate_field(field_path, value, rule)
                if not is_valid:
                    errors.append(error)
            except KeyError:
                if rule.required:
                    errors.append(f"Required field '{field_path}' is missing")
        
        return len(errors) == 0, errors
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Path '{path}' not found")
        
        return current
    
    def _validate_field(self, field_path: str, value: Any, 
                       rule: ValidationRule) -> tuple[bool, str]:
        """Validate a single field against its rule"""
        
        # Check if required field is None
        if rule.required and value is None:
            return False, f"Field '{field_path}' is required but is None"
        
        # Skip validation for optional None values
        if not rule.required and value is None:
            return True, ""
        
        # Type validation
        if not isinstance(value, rule.field_type):
            return False, (f"Field '{field_path}' must be of type "
                          f"{rule.field_type.__name__}, got {type(value).__name__}")
        
        # Range validation for numbers
        if rule.min_value is not None and value < rule.min_value:
            return False, (f"Field '{field_path}' must be >= {rule.min_value}, "
                          f"got {value}")
        
        if rule.max_value is not None and value > rule.max_value:
            return False, (f"Field '{field_path}' must be <= {rule.max_value}, "
                          f"got {value}")
        
        # Allowed values validation
        if rule.allowed_values is not None and value not in rule.allowed_values:
            return False, (f"Field '{field_path}' must be one of "
                          f"{rule.allowed_values}, got {value}")
        
        # Pattern validation for strings
        if rule.pattern is not None and isinstance(value, str):
            import re
            if not re.match(rule.pattern, value):
                return False, (f"Field '{field_path}' does not match "
                              f"required pattern: {rule.pattern}")
        
        # Custom validator function
        if rule.validator_func is not None:
            try:
                is_valid, error_msg = rule.validator_func(value)
                if not is_valid:
                    return False, f"Field '{field_path}': {error_msg}"
            except Exception as e:
                return False, (f"Field '{field_path}' validation failed: "
                              f"{str(e)}")
        
        return True, ""

def create_jan_assistant_schema() -> ConfigSchema:
    """Create the configuration schema for Jan Assistant Pro"""
    schema = ConfigSchema()
    
    # API configuration
    schema.add_rule('api.base_url', ValidationRule(
        field_type=str,
        required=True,
        pattern=r'^https?://.+',
        description="API base URL (must be valid HTTP/HTTPS URL)"
    ))
    
    schema.add_rule('api.api_key', ValidationRule(
        field_type=str,
        required=True,
        description="API authentication key"
    ))
    
    schema.add_rule('api.model', ValidationRule(
        field_type=str,
        required=True,
        description="Model name to use for API calls"
    ))
    
    schema.add_rule('api.timeout', ValidationRule(
        field_type=int,
        required=False,
        default=30,
        min_value=1,
        max_value=300,
        description="API timeout in seconds (1-300)"
    ))
    
    # Memory configuration
    schema.add_rule('memory.file', ValidationRule(
        field_type=str,
        required=True,
        description="Path to memory storage file"
    ))
    
    schema.add_rule('memory.max_entries', ValidationRule(
        field_type=int,
        required=False,
        default=1000,
        min_value=10,
        max_value=100000,
        description="Maximum number of memory entries (10-100000)"
    ))
    
    schema.add_rule('memory.auto_save', ValidationRule(
        field_type=bool,
        required=False,
        default=True,
        description="Whether to automatically save memory changes"
    ))
    
    # UI configuration
    schema.add_rule('ui.theme', ValidationRule(
        field_type=str,
        required=False,
        default="dark",
        allowed_values=["dark", "light"],
        description="UI theme (dark or light)"
    ))
    
    schema.add_rule('ui.window_size', ValidationRule(
        field_type=str,
        required=False,
        default="800x600",
        pattern=r'^\d+x\d+$',
        description="Window size in format 'WIDTHxHEIGHT'"
    ))
    
    schema.add_rule('ui.font_family', ValidationRule(
        field_type=str,
        required=False,
        default="Consolas",
        description="Font family for UI text"
    ))
    
    schema.add_rule('ui.font_size', ValidationRule(
        field_type=int,
        required=False,
        default=10,
        min_value=6,
        max_value=24,
        description="Font size for UI text (6-24)"
    ))
    
    # Security configuration
    schema.add_rule('security.allowed_commands', ValidationRule(
        field_type=list,
        required=False,
        default=["ls", "pwd", "cat", "echo", "python3", "python", "ping"],
        description="List of allowed system commands"
    ))
    
    schema.add_rule('security.restricted_paths', ValidationRule(
        field_type=list,
        required=False,
        default=["/etc", "/sys", "/proc"],
        description="List of restricted file system paths"
    ))
    
    schema.add_rule('security.max_file_size', ValidationRule(
        field_type=str,
        required=False,
        default="10MB",
        pattern=r'^\d+[KMGT]?B$',
        description="Maximum file size (e.g., '10MB', '1GB')"
    ))
    
    return schema

def validate_file_path(path: str) -> tuple[bool, str]:
    """Validate that a file path is accessible"""
    try:
        path_obj = Path(path)
        parent_dir = path_obj.parent
        
        # Check if parent directory exists or can be created
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return False, f"Cannot create directory: {parent_dir}"
        
        # Check if file is writable (if it exists) or directory is writable
        if path_obj.exists():
            if not os.access(path, os.W_OK):
                return False, f"File is not writable: {path}"
        else:
            if not os.access(parent_dir, os.W_OK):
                return False, f"Directory is not writable: {parent_dir}"
        
        return True, ""
    except Exception as e:
        return False, f"Invalid file path: {str(e)}"

def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL format and accessibility"""
    import re
    from urllib.parse import urlparse
    
    # Basic URL format validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False, "Invalid URL format"
    
    # Parse URL components
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "URL must have scheme and netloc"
    except Exception as e:
        return False, f"URL parsing error: {str(e)}"
    
    return True, ""

class ConfigValidator:
    """Main configuration validator class"""
    
    def __init__(self, schema: ConfigSchema = None):
        """
        Initialize validator with schema
        
        Args:
            schema: Configuration schema to use
        """
        self.schema = schema or create_jan_assistant_schema()
    
    def validate_config_file(self, config_path: str) -> Dict[str, Any]:
        """
        Validate configuration file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigurationError: If validation fails
        """
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Error reading config file: {str(e)}")
        
        return self.validate_config_data(config_data)
    
    def validate_config_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration data
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            Validated and normalized configuration
            
        Raises:
            ValidationError: If validation fails
        """
        is_valid, errors = self.schema.validate(config_data)
        
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            raise ValidationError(error_msg)
        
        # Apply defaults for missing optional fields
        normalized_config = self._apply_defaults(config_data)
        
        return normalized_config
    
    def _apply_defaults(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing optional fields"""
        import copy
        normalized = copy.deepcopy(config_data)
        
        for field_path, rule in self.schema.rules.items():
            if not rule.required and rule.default is not None:
                try:
                    self.schema._get_nested_value(normalized, field_path)
                except KeyError:
                    # Field is missing, apply default
                    self._set_nested_value(normalized, field_path, rule.default)
        
        return normalized
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def generate_schema_documentation(self) -> str:
        """Generate human-readable schema documentation"""
        doc = "# Configuration Schema Documentation\n\n"
        
        # Group rules by section
        sections = {}
        for field_path, rule in self.schema.rules.items():
            section = field_path.split('.')[0]
            if section not in sections:
                sections[section] = []
            sections[section].append((field_path, rule))
        
        for section, fields in sections.items():
            doc += f"## {section.title()} Configuration\n\n"
            
            for field_path, rule in fields:
                doc += f"### `{field_path}`\n\n"
                doc += f"**Type:** {rule.field_type.__name__}\n"
                doc += f"**Required:** {'Yes' if rule.required else 'No'}\n"
                
                if rule.default is not None:
                    doc += f"**Default:** `{rule.default}`\n"
                
                if rule.allowed_values:
                    doc += f"**Allowed values:** {rule.allowed_values}\n"
                
                if rule.min_value is not None or rule.max_value is not None:
                    range_str = ""
                    if rule.min_value is not None:
                        range_str += f"min: {rule.min_value}"
                    if rule.max_value is not None:
                        if range_str:
                            range_str += ", "
                        range_str += f"max: {rule.max_value}"
                    doc += f"**Range:** {range_str}\n"
                
                if rule.pattern:
                    doc += f"**Pattern:** `{rule.pattern}`\n"
                
                if rule.description:
                    doc += f"**Description:** {rule.description}\n"
                
                doc += "\n"
        
        return doc
