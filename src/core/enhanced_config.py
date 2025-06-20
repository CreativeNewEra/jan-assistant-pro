"""Enhanced configuration with environment support"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Optional

from .config import Config


class EnhancedConfig(Config):
    """Configuration with environment variable support"""

    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        # Load environment variables
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=True)
        super().__init__(config_path=config_path)

    def get(self, key_path: str, default: Any = None):
        """Get config value with environment variable override"""
        env_key = f"JAN_ASSISTANT_{key_path.replace('.', '_').upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        return super().get(key_path, default)

    def _convert_env_value(self, value: str):
        """Convert environment variable string to appropriate type"""
        lower = value.lower()
        if lower in ("true", "false"):
            return lower == "true"
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
        if value.startswith(("[", "{")):
            try:
                import json

                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return value
