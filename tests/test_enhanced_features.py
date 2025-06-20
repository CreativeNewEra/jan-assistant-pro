"""
Comprehensive tests for enhanced Jan Assistant Pro features
Tests the new tool registry, error handling, and configuration validation
"""

import json
import os
import sys
import tempfile
from typing import Any, Dict
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.config_validator import (
    ConfigSchema,
    ConfigValidator,
    ValidationRule,
    create_jan_assistant_schema,
)
from src.core.exceptions import (
    APIError,
    ConfigurationError,
    JanAssistantError,
    ToolError,
    ValidationError,
    handle_exception,
)
from src.tools.base_tool import BaseTool, ToolInfo, ToolParameter
from src.tools.tool_registry import ToolRegistry, ToolRegistryError


class MockTool(BaseTool):
    """Mock tool for testing purposes"""
    
    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="mock_tool",
            description="A mock tool for testing",
            category="testing",
            parameters=[
                ToolParameter("input", "Test input", str, required=True),
                ToolParameter("count", "Number of times", int, required=False, default=1)
            ],
            examples=["mock_tool with input='test'"]
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        input_text = kwargs.get('input', '')
        count = kwargs.get('count', 1)
        
        if input_text == 'error':
            return self._create_error_response("Mock error occurred")
        
        result = input_text * count
        return self._create_success_response(result, {'processed_count': count})

class InvalidTool:
    """Tool that doesn't inherit from BaseTool"""
    pass

class TestToolRegistry(unittest.TestCase):
    """Test cases for the tool registry system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = ToolRegistry()
    
    def test_register_valid_tool(self):
        """Test registering a valid tool"""
        self.registry.register_tool(MockTool)
        
        # Check tool is registered
        self.assertIn("mock_tool", self.registry.list_tools())
        
        # Check tool info is stored
        tool_info = self.registry.get_tool_info("mock_tool")
        self.assertIsNotNone(tool_info)
        self.assertEqual(tool_info.name, "mock_tool")
        self.assertEqual(tool_info.category, "testing")
    
    def test_register_invalid_tool(self):
        """Test registering invalid tool raises error"""
        with self.assertRaises(ToolRegistryError):
            self.registry.register_tool(InvalidTool)
    
    def test_register_duplicate_tool(self):
        """Test registering duplicate tool raises error"""
        self.registry.register_tool(MockTool)
        
        with self.assertRaises(ToolRegistryError):
            self.registry.register_tool(MockTool)
    
    def test_execute_tool_success(self):
        """Test successful tool execution"""
        self.registry.register_tool(MockTool)
        
        result = self.registry.execute_tool("mock_tool", input="hello", count=2)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['result'], "hellohello")
        self.assertEqual(result['metadata']['processed_count'], 2)
    
    def test_execute_tool_validation_error(self):
        """Test tool execution with invalid parameters"""
        self.registry.register_tool(MockTool)
        
        # Missing required parameter
        result = self.registry.execute_tool("mock_tool", count=2)
        self.assertFalse(result['success'])
        self.assertIn("validation failed", result['error'])
    
    def test_execute_tool_not_found(self):
        """Test executing non-existent tool"""
        result = self.registry.execute_tool("nonexistent_tool")
        
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        self.assertIn("available_tools", result)
    
    def test_unregister_tool(self):
        """Test unregistering a tool"""
        self.registry.register_tool(MockTool)
        self.assertIn("mock_tool", self.registry.list_tools())
        
        self.registry.unregister_tool("mock_tool")
        self.assertNotIn("mock_tool", self.registry.list_tools())
    
    def test_list_tools_by_category(self):
        """Test listing tools by category"""
        self.registry.register_tool(MockTool)
        
        testing_tools = self.registry.list_tools(category="testing")
        self.assertIn("mock_tool", testing_tools)
        
        other_tools = self.registry.list_tools(category="other")
        self.assertEqual(len(other_tools), 0)
    
    def test_generate_help(self):
        """Test help generation"""
        self.registry.register_tool(MockTool)
        
        # Test help for specific tool
        tool_help = self.registry.generate_help("mock_tool")
        self.assertIn("mock_tool", tool_help)
        self.assertIn("A mock tool for testing", tool_help)
        
        # Test help for all tools
        all_help = self.registry.generate_help()
        self.assertIn("Available Tools", all_help)
        self.assertIn("Testing", all_help)
    
    def test_registry_stats(self):
        """Test registry statistics"""
        self.registry.register_tool(MockTool)
        
        stats = self.registry.get_registry_stats()
        self.assertEqual(stats['total_tools'], 1)
        self.assertEqual(stats['category_count'], 1)
        self.assertIn('testing', stats['categories'])

class TestExceptionHandling(unittest.TestCase):
    """Test cases for enhanced exception handling"""
    
    def test_jan_assistant_error_creation(self):
        """Test creating custom exceptions"""
        error = JanAssistantError(
            "Test error", 
            error_code="TEST_ERROR",
            context={"test_field": "test_value"}
        )
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, "TEST_ERROR")
        self.assertEqual(error.context["test_field"], "test_value")
    
    def test_exception_to_dict(self):
        """Test exception serialization"""
        error = APIError(
            "API failed",
            status_code=500,
            response_data="Internal server error"
        )
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['error_type'], 'APIError')
        self.assertEqual(error_dict['message'], 'API failed')
        self.assertEqual(error_dict['context']['status_code'], 500)
    
    def test_handle_custom_exception(self):
        """Test handling custom exceptions"""
        error = ValidationError("Invalid input", field_name="test_field")
        result = handle_exception(error)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['error_type'], 'ValidationError')
        self.assertEqual(result['error']['context']['field_name'], 'test_field')
    
    def test_handle_standard_exception(self):
        """Test handling standard Python exceptions"""
        error = ValueError("Standard error")
        result = handle_exception(error)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error']['error_type'], 'UnexpectedError')
        self.assertEqual(result['error']['message'], 'Standard error')

class TestConfigurationValidation(unittest.TestCase):
    """Test cases for configuration validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ConfigValidator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_configuration(self):
        """Test validation of valid configuration"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model",
                "timeout": 30
            },
            "memory": {
                "file": "test_memory.json",
                "max_entries": 1000,
                "auto_save": True
            },
            "ui": {
                "theme": "dark",
                "window_size": "800x600",
                "font_family": "Arial",
                "font_size": 12
            },
            "security": {
                "allowed_commands": ["ls", "pwd"],
                "restricted_paths": ["/etc"],
                "max_file_size": "10MB"
            }
        }
        
        # Should not raise any exceptions
        normalized_config = self.validator.validate_config_data(config_data)
        self.assertIsNotNone(normalized_config)
    
    def test_missing_required_field(self):
        """Test validation with missing required field"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                # Missing required api_key
                "model": "test_model"
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_config_data(config_data)
        
        self.assertIn("api_key", str(cm.exception))
    
    def test_invalid_field_type(self):
        """Test validation with invalid field type"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model",
                "timeout": "not_a_number"  # Should be int
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_config_data(config_data)
        
        self.assertIn("timeout", str(cm.exception))
        self.assertIn("int", str(cm.exception))
    
    def test_value_out_of_range(self):
        """Test validation with value out of allowed range"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model",
                "timeout": 500  # Should be <= 300
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_config_data(config_data)
        
        self.assertIn("timeout", str(cm.exception))
        self.assertIn("300", str(cm.exception))
    
    def test_invalid_pattern(self):
        """Test validation with pattern mismatch"""
        config_data = {
            "api": {
                "base_url": "invalid_url",  # Should match HTTP pattern
                "api_key": "test_key",
                "model": "test_model"
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_config_data(config_data)
        
        self.assertIn("base_url", str(cm.exception))
    
    def test_invalid_allowed_value(self):
        """Test validation with invalid allowed value"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model"
            },
            "ui": {
                "theme": "purple"  # Should be 'dark' or 'light'
            }
        }
        
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_config_data(config_data)
        
        self.assertIn("theme", str(cm.exception))
    
    def test_apply_defaults(self):
        """Test that default values are applied"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model"
                # timeout not specified, should get default
            },
            "memory": {
                "file": "test_memory.json"
                # max_entries not specified, should get default
            }
        }
        
        normalized_config = self.validator.validate_config_data(config_data)
        
        # Check defaults were applied
        self.assertEqual(normalized_config['api']['timeout'], 30)
        self.assertEqual(normalized_config['memory']['max_entries'], 1000)
    
    def test_config_file_validation(self):
        """Test validating configuration from file"""
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model"
            },
            "memory": {
                "file": "test_memory.json"
            }
        }
        
        # Create temporary config file
        config_file = os.path.join(self.temp_dir, "test_config.json")
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Should validate successfully
        normalized_config = self.validator.validate_config_file(config_file)
        self.assertIsNotNone(normalized_config)
    
    def test_invalid_json_file(self):
        """Test handling of invalid JSON file"""
        config_file = os.path.join(self.temp_dir, "invalid_config.json")
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(ConfigurationError) as cm:
            self.validator.validate_config_file(config_file)
        
        self.assertIn("Invalid JSON", str(cm.exception))
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.json")
        
        with self.assertRaises(ConfigurationError) as cm:
            self.validator.validate_config_file(nonexistent_file)
        
        self.assertIn("not found", str(cm.exception))
    
    def test_schema_documentation_generation(self):
        """Test schema documentation generation"""
        doc = self.validator.generate_schema_documentation()
        
        self.assertIn("Configuration Schema Documentation", doc)
        self.assertIn("Api Configuration", doc)
        self.assertIn("api.base_url", doc)
        self.assertIn("Type:", doc)
        self.assertIn("Required:", doc)

class TestIntegration(unittest.TestCase):
    """Integration tests for enhanced features"""
    
    def test_tool_registry_with_exception_handling(self):
        """Test tool registry handles exceptions properly"""
        registry = ToolRegistry()
        registry.register_tool(MockTool)
        
        # Test tool that returns error
        result = registry.execute_tool("mock_tool", input="error")
        self.assertFalse(result['success'])
        self.assertIn("Mock error occurred", result['error'])
    
    def test_config_validation_with_tool_registry(self):
        """Test that validated config can be used with tools"""
        validator = ConfigValidator()
        
        config_data = {
            "api": {
                "base_url": "http://localhost:1337/v1",
                "api_key": "test_key",
                "model": "test_model"
            },
            "memory": {
                "file": "test_memory.json"
            },
            "security": {
                "allowed_commands": ["test_command"],
                "max_file_size": "5MB"
            }
        }
        
        normalized_config = validator.validate_config_data(config_data)
        
        # Use config with tool
        registry = ToolRegistry()
        registry.register_tool(MockTool, normalized_config)
        
        # Tool should be registered successfully
        self.assertIn("mock_tool", registry.list_tools())

if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run tests
    unittest.main(verbosity=2)
