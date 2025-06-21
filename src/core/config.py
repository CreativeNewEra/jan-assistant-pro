"""
Configuration management for Jan Assistant Pro
"""

import json
import os
import time
from typing import Any, Dict

from cachetools import TTLCache

from .logging_config import get_logger


class Config:
    """Configuration manager for the application"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._find_config_path()
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"config_path": self.config_path},
        )
        self._cache: TTLCache | None = None
        self._last_load: float = 0.0
        self.config_data = self._load_config()
        self._init_cache()

    def _find_config_path(self) -> str:
        """Find the configuration file path"""
        # Look for config in several locations
        possible_paths = [
            os.path.join(os.getcwd(), "config", "config.json"),
            os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "config.json"
            ),
            os.path.expanduser("~/.jan-assistant-pro/config.json"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Return the first option as default
        return possible_paths[0]

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self._cache is not None:
            cached = self._cache.get(self.config_path)
            if cached is not None:
                self._last_load = cached["timestamp"]
                return cached["data"]

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(
                    "Could not load config file",
                    extra={"extra_fields": {"error": str(e), "path": self.config_path}},
                )
                data = self._get_default_config()
        else:
            data = self._get_default_config()
            self._ensure_config_dir()
            self.save_config(data)

        self._last_load = time.time()
        if self._cache is not None:
            self._cache[self.config_path] = {
                "data": data,
                "timestamp": self._last_load,
            }
        return data

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "api": {
                "base_url": "http://127.0.0.1:1337/v1",
                "api_key": "124578",
                "model": "qwen3:30b-a3b",
                "timeout": 30,
                "cache_enabled": False,
                "cache_ttl": 300,
                "cache_size": 128,
                "circuit_breaker": {"fail_max": 3, "reset_timeout": 60},
            },
            "memory": {
                "file": "data/memory.json",
                "max_entries": 1000,
                "auto_save": True,
            },
            "ui": {
                "theme": "dark",
                "window_size": "800x600",
                "font_family": "Consolas",
                "font_size": 10,
            },
            "tools": {
                "file_operations": True,
                "system_commands": True,
                "memory_operations": True,
                "web_search": False,
            },
            "security": {
                "allowed_commands": [
                    "ls",
                    "pwd",
                    "cat",
                    "echo",
                    "python3",
                    "python",
                    "ping",
                ],
                "restricted_paths": ["/etc", "/sys", "/proc"],
                "max_file_size": "10MB",
            },
            "cache": {
                "api": {"size": 128, "ttl": 300},
                "disk": {"dir": "data/cache", "ttl": 3600},
                "config": {"ttl": 300, "size": 4},
            },
        }

    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

    def _init_cache(self) -> None:
        cache_cfg = self.config_data.get("cache", {}).get("config", {})
        size = int(cache_cfg.get("size", 4))
        ttl = int(cache_cfg.get("ttl", 300))
        self._cache = TTLCache(maxsize=size, ttl=ttl)
        self._cache[self.config_path] = {
            "data": self.config_data,
            "timestamp": self._last_load,
        }

    def _check_reload(self) -> None:
        if self._cache is not None and self._cache.get(self.config_path) is None:
            self.reload()

    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'api.base_url')"""
        self._check_reload()
        keys = key_path.split(".")
        value = self.config_data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        self._check_reload()
        keys = key_path.split(".")
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
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            self.logger.warning(
                "Could not save config file",
                extra={"extra_fields": {"error": str(e), "path": self.config_path}},
            )

    def reload(self):
        """Reload configuration from file"""
        if self._cache is not None:
            self._cache.pop(self.config_path, None)
        self.config_data = self._load_config()
        self._init_cache()

    # Convenience properties for common config values
    @property
    def api_base_url(self) -> str:
        return self.get("api.base_url", "http://127.0.0.1:1337/v1")

    @property
    def api_key(self) -> str:
        return self.get("api.api_key", "124578")

    @property
    def model_name(self) -> str:
        return self.get("api.model", "qwen3:30b-a3b")

    @property
    def memory_file(self) -> str:
        return self.get("memory.file", "data/memory.json")

    @property
    def window_size(self) -> str:
        return self.get("ui.window_size", "800x600")

    @property
    def theme(self) -> str:
        return self.get("ui.theme", "dark")

    @property
    def cache_enabled(self) -> bool:
        return bool(self.get("api.cache_enabled", False))

    @property
    def cache_ttl(self) -> int:
        return int(self.get("api.cache_ttl", 300))

    @property
    def cache_size(self) -> int:
        return int(self.get("api.cache_size", 128))

    @property
    def breaker_fail_max(self) -> int:
        return int(self.get("api.circuit_breaker.fail_max", 3))

    @property
    def breaker_reset_timeout(self) -> int:
        return int(self.get("api.circuit_breaker.reset_timeout", 60))

    @property
    def config_cache_ttl(self) -> int:
        cache_cfg = self.get("cache.config.ttl", 300)
        return int(cache_cfg)

    @property
    def config_cache_size(self) -> int:
        cache_cfg = self.get("cache.config.size", 4)
        return int(cache_cfg)

    @property
    def last_loaded(self) -> float:
        return self._last_load

    def __str__(self):
        return f"Config(path={self.config_path})"
