"""Secure configuration using environment variables and keyring."""

from __future__ import annotations

import os
from getpass import getpass

import keyring

from .config import Config


class SecureConfig(Config):
    """Configuration that retrieves the API key securely."""

    def _prompt_for_key(self) -> str:
        """Prompt the user for the API key."""
        return getpass("Enter Jan API key: ")

    @property
    def api_key(self) -> str:  # type: ignore[override]
        """Return the API key from env, keyring or user prompt."""
        key = os.environ.get("JAN_API_KEY")
        if key:
            return key

        try:
            key = keyring.get_password("jan-assistant", "api-key")
            if key:
                return key
        except Exception:
            # Fall back to prompt if keyring fails
            key = None

        key = self._prompt_for_key()
        try:
            keyring.set_password("jan-assistant", "api-key", key)
        except Exception:
            pass
        return key
