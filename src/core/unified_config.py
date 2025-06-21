"""Unified configuration system for Jan Assistant Pro"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from cachetools import TTLCache
from dotenv import load_dotenv

from .config_validator import ConfigValidator
from .logging_config import get_logger
from .event_manager import EventManager

ENV_PREFIX = "JAN_ASSISTANT_"


class UnifiedConfig:
    """Configuration manager with validation and env overrides."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        env_file: Optional[str] = None,
        schema: Optional[ConfigValidator] = None,
        event_manager: EventManager | None = None,
    ) -> None:
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=True)

        self.config_path = config_path or self._find_config_path()
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"config_path": self.config_path},
        )
        self.validator = schema or ConfigValidator()
        self.event_manager = event_manager
        self.config_data: Dict[str, Any] = {}
        self._cache: TTLCache | None = None
        self._last_load: float = 0.0
        self.reload()
        self._init_cache()

    def _find_config_path(self) -> str:
        possible_paths = [
            os.path.join(os.getcwd(), "config", "config.json"),
            os.path.join(
                Path(__file__).resolve().parent.parent, "config", "config.json"
            ),
            os.path.expanduser("~/.jan-assistant-pro/config.json"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]

    def _ensure_config_dir(self) -> None:
        config_dir = os.path.dirname(self.config_path)
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

    def _get_default_config(self) -> Dict[str, Any]:
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

    # ------------------------------------------------------------------
    # Loading and validation
    # ------------------------------------------------------------------
    def reload(self) -> None:
        if self._cache is not None:
            self._cache.pop(self.config_path, None)
        self.config_data = self._load_config()
        self._init_cache()
        if self.event_manager:
            self.event_manager.emit("config_reloaded", path=self.config_path)

    def _load_config(self) -> Dict[str, Any]:
        if self._cache is not None:
            cached = self._cache.get(self.config_path)
            if cached is not None:
                self._last_load = cached["timestamp"]
                return cached["data"]

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                self.logger.warning(
                    "Could not load config file",
                    extra={"extra_fields": {"error": str(e), "path": self.config_path}},
                )
                data = self._get_default_config()
        else:
            data = self._get_default_config()
            self._ensure_config_dir()
            self.save_config(data)

        data = self._apply_env_overrides(data)
        validated = self.validator.validate_config_data(data)
        self._last_load = time.time()
        if self._cache is not None:
            self._cache[self.config_path] = {
                "data": validated,
                "timestamp": self._last_load,
            }
        return validated

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        for field_path in self.validator.schema.rules.keys():
            env_key = ENV_PREFIX + field_path.replace(".", "_").upper()
            if env_key in os.environ:
                value = self._convert_env_value(os.environ[env_key])
                self._set_nested_value(config_data, field_path, value)
        return config_data

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _convert_env_value(self, value: str) -> Any:
        lower = value.lower()
        if lower in ("true", "false"):
            return lower == "true"
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
        if value.startswith("[") or value.startswith("{"):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, key_path: str, default: Any = None) -> Any:
        self._check_reload()
        keys = key_path.split(".")
        value: Any = self.config_data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        self._check_reload()
        self._set_nested_value(self.config_data, key_path, value)
        if self.event_manager:
            self.event_manager.emit("config_changed", key=key_path, value=value)

    def save_config(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        data = config_data or self.config_data
        self._ensure_config_dir()
        tmp_path = self.config_path + ".tmp"
        backup_path = self.config_path + ".bak"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if os.path.exists(self.config_path):
                shutil.copy2(self.config_path, backup_path)
            os.replace(tmp_path, self.config_path)
            if self.event_manager:
                self.event_manager.emit("config_saved", path=self.config_path)
        except OSError as e:
            self.logger.warning(
                "Could not save config file",
                extra={"extra_fields": {"error": str(e), "path": self.config_path}},
            )
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.config_path)
            raise

    def restore_backup(self) -> bool:
        backup_path = self.config_path + ".bak"
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, self.config_path)
            self.reload()
            if self.event_manager:
                self.event_manager.emit("config_restored", path=self.config_path)
            return True
        return False

    def __str__(self) -> str:
        return f"UnifiedConfig(path={self.config_path})"

    @property
    def config_cache_ttl(self) -> int:
        return int(self.get("cache.config.ttl", 300))

    @property
    def config_cache_size(self) -> int:
        return int(self.get("cache.config.size", 4))

    @property
    def breaker_fail_max(self) -> int:
        return int(self.get("api.circuit_breaker.fail_max", 3))

    @property
    def breaker_reset_timeout(self) -> int:
        return int(self.get("api.circuit_breaker.reset_timeout", 60))

    @property
    def last_loaded(self) -> float:
        return self._last_load
