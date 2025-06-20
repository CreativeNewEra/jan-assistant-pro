"""
Configuration management for Jan Assistant Pro
"""

import json
import os
from typing import Any, Dict


class Config:
    """Configuration manager for the application"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._find_config_path()
        self.config_data = self._load_config()
    
    def _find_config_path(self) -> str:
        """Find the configuration file path"""
        # Look for config in several locations
        possible_paths = [
            os.path.join(os.getcwd(), 'config', 'config.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json'),
            os.path.expanduser('~/.jan-assistant-pro/config.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return the first option as default
        return possible_paths[0]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                return self._get_default_config()
        else:
            # Create default config
            config = self._get_default_config()
            self._ensure_config_dir()
            self.save_config(config)
            return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "api": {
                "base_url": "http://127.0.0.1:1337/v1",
                "api_key": "124578",
                "model": "qwen3:30b-a3b",
                "timeout": 30
            },
            "memory": {
                "file": "data/memory.json",
                "max_entries": 1000,
                "auto_save": True
            },
            "ui": {
                "theme": "dark",
                "window_size": "800x600",
                "font_family": "Consolas",
                "font_size": 10
            },
            "tools": {
                "file_operations": True,
                "system_commands": True,
                "memory_operations": True,
                "web_search": False
            },
            "security": {
                "allowed_commands": ["ls", "pwd", "cat", "echo", "python3", "python", "ping"],
                "restricted_paths": ["/etc", "/sys", "/proc"],
                "max_file_size": "10MB"
            }
        }
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'api.base_url')"""
        keys = key_path.split('.')
        value = self.config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the final value
        config[keys[-1]] = value
    
    def save_config(self, config_data: Dict[str, Any] = None):
        """Save configuration to file"""
        data = config_data or self.config_data
        self._ensure_config_dir()
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save config to {self.config_path}: {e}")
    
    def reload(self):
        """Reload configuration from file"""
        self.config_data = self._load_config()
    
    # Convenience properties for common config values
    @property
    def api_base_url(self) -> str:
        return self.get('api.base_url', 'http://127.0.0.1:1337/v1')
    
    @property
    def api_key(self) -> str:
        return self.get('api.api_key', '124578')
    
    @property
    def model_name(self) -> str:
        return self.get('api.model', 'qwen3:30b-a3b')
    
    @property
    def memory_file(self) -> str:
        return self.get('memory.file', 'data/memory.json')
    
    @property
    def window_size(self) -> str:
        return self.get('ui.window_size', '800x600')
    
    @property
    def theme(self) -> str:
        return self.get('ui.theme', 'dark')
    
    def __str__(self):
        return f"Config(path={self.config_path})"
