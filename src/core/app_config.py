from __future__ import annotations

import json
import os
import dataclasses
from dataclasses import asdict, dataclass, field
import typing
from typing import Any, Dict, Optional

ENV_PREFIX = "JAN_ASSISTANT_"
CONFIG_ENV_VAR = "JAN_ASSISTANT_CONFIG_FILE"

SAFE_INFO_COMMANDS = ["ls", "pwd", "date", "whoami", "echo"]
SAFE_READ_COMMANDS = ["cat", "head", "tail", "grep"]  # Still dangerous!


@dataclass
class APIConfig:
    base_url: str = "http://127.0.0.1:1337/v1"
    api_key: str = "124578"
    model: str = "qwen3:30b-a3b"
    timeout: int = 30


@dataclass
class SecurityConfig:
    allowed_commands: list[str] = field(
        default_factory=lambda: SAFE_INFO_COMMANDS + SAFE_READ_COMMANDS
    )
    restricted_paths: list[str] = field(
        default_factory=lambda: ["/etc", "/sys", "/proc"]
    )
    max_file_size: str = "10MB"


@dataclass
class UIConfig:
    theme: str = "dark"
    window_size: str = "800x600"
    font_family: str = "Consolas"
    font_size: int = 10


@dataclass
class AppConfig:
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    @classmethod
    def load(cls) -> "AppConfig":
        # 1. Load defaults
        config = cls._defaults()

        # 2. Merge with file
        if file_config := cls._load_file():
            config = cls._merge(config, file_config)

        # 3. Override with env vars
        config = cls._apply_env_overrides(config)

        # 4. Validate
        cls._validate(config)

        return config

    @staticmethod
    def _get_field_paths(cls, prefix: str = "") -> List[str]:
        paths: List[str] = []
        type_hints = typing.get_type_hints(cls)
        for name, hint in type_hints.items():
            full = f"{prefix}{name}"
            if dataclasses.is_dataclass(hint):
                paths.extend(AppConfig._get_field_paths(hint, full + "."))
            else:
                paths.append(full)
        return paths

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _defaults() -> "AppConfig":
        return AppConfig()

    @staticmethod
    def _load_file() -> Optional[Dict[str, Any]]:
        path = os.environ.get(CONFIG_ENV_VAR)
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load configuration from {path}: {e}")
                return None

        default_path = os.path.join(os.getcwd(), "config", "config.json")
        if os.path.exists(default_path):
            try:
                with open(default_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @staticmethod
    def _merge(base: "AppConfig", override: Dict[str, Any]) -> "AppConfig":
        data = asdict(base)
        AppConfig._deep_update(data, override)
        return AppConfig._from_dict(data)

    @staticmethod
    def _deep_update(dest: Dict[str, Any], src: Dict[str, Any]) -> None:
        for key, value in src.items():
            if (
                key in dest
                and isinstance(dest[key], dict)
                and isinstance(value, dict)
            ):
                AppConfig._deep_update(dest[key], value)
            else:
                dest[key] = value

    @staticmethod
    def _from_dict(data: Dict[str, Any]) -> "AppConfig":
        def _filter(d: Dict[str, Any], cls: type) -> Dict[str, Any]:
            allowed = typing.get_type_hints(cls).keys()
            return {k: v for k, v in d.items() if k in allowed}

        return AppConfig(
            api=APIConfig(**_filter(data.get("api", {}), APIConfig)),
            security=SecurityConfig(**_filter(data.get("security", {}), SecurityConfig)),
            ui=UIConfig(**_filter(data.get("ui", {}), UIConfig)),
        )

    @staticmethod
    def _apply_env_overrides(config: "AppConfig") -> "AppConfig":
        data = asdict(config)
        fields = AppConfig._get_field_paths(AppConfig)
        for path in fields:
            env_key = ENV_PREFIX + path.replace(".", "_").upper()
            if env_key in os.environ:
                value = AppConfig._convert_env(os.environ[env_key])
                AppConfig._set_nested_value(data, path, value)
        return AppConfig._from_dict(data)

    @staticmethod
    def _convert_env(value: str) -> Any:
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

    @staticmethod
    def _set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
        keys = path.split(".")
        d = data
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    @staticmethod
    def _validate(config: "AppConfig") -> None:
        if not config.api.base_url:
            raise ValueError("api.base_url is required")
        if not config.api.api_key:
            raise ValueError("api.api_key is required")
        if not config.api.model:
            raise ValueError("api.model is required")
        if config.api.timeout <= 0:
            raise ValueError("api.timeout must be positive")
        if config.ui.theme not in ("dark", "light"):
            raise ValueError("ui.theme must be 'dark' or 'light'")
        if config.ui.font_size <= 0:
            raise ValueError("ui.font_size must be positive")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

