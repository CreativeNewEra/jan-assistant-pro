import os
import sys
from unittest.mock import patch

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.core.secure_config import SecureConfig


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("JAN_API_KEY", "envvalue")
    cfg = SecureConfig()
    assert cfg.api_key == "envvalue"


def test_api_key_from_keyring(monkeypatch):
    monkeypatch.delenv("JAN_API_KEY", raising=False)
    with patch("keyring.get_password", return_value="ring") as get_pw:
        cfg = SecureConfig()
        assert cfg.api_key == "ring"
        get_pw.assert_called_once_with("jan-assistant", "api-key")


def test_api_key_prompt_and_store(monkeypatch):
    monkeypatch.delenv("JAN_API_KEY", raising=False)
    with patch("keyring.get_password", return_value=None):
        with patch("keyring.set_password") as set_pw:

            class TestConfig(SecureConfig):
                def _prompt_for_key(self) -> str:  # type: ignore[override]
                    return "prompt"

            cfg = TestConfig()
            assert cfg.api_key == "prompt"
            set_pw.assert_called_once_with("jan-assistant", "api-key", "prompt")
