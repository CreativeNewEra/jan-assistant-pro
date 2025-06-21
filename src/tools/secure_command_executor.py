"""Secure command execution with sandboxing and resource limits"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from src.core.logging_config import get_logger

try:
    import resource
except Exception:  # pragma: no cover
    resource = None  # type: ignore


class SecureCommandExecutor:
    """Execute system commands with strict security controls."""

    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None,
        timeout: int = 30,
        max_output_bytes: int = 10_000,
        work_dir: Optional[str] = None,
    ) -> None:
        self.allowed_commands = allowed_commands or ["ls", "pwd", "echo", "cat", "ping"]
        self.blocked_commands = blocked_commands or ["rm", "shutdown", "reboot"]
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self._base_temp_dir: Optional[tempfile.TemporaryDirectory] = None
        if work_dir:
            self.base_work_dir = work_dir
        else:
            self._base_temp_dir = tempfile.TemporaryDirectory(prefix="jan_sandbox_")
            self.base_work_dir = self._base_temp_dir.name
        os.makedirs(self.base_work_dir, exist_ok=True)
        self.logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            {"timeout": self.timeout, "work_dir": self.base_work_dir},
        )

    def __enter__(self) -> "SecureCommandExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._base_temp_dir is not None:
            try:
                self._base_temp_dir.cleanup()
            except Exception:  # pragma: no cover - best effort
                pass

    def _command_name(self, command: str) -> str:
        parts = shlex.split(command)
        return parts[0] if parts else ""

    def _validate_command(self, command: str) -> Optional[str]:
        base = self._command_name(command)
        if base in self.blocked_commands:
            return f"Command '{base}' is blocked"
        if base not in self.allowed_commands:
            return f"Command '{base}' is not allowed"
        if re.search(r"&&|;|`|\$\(|\|", command):
            return "Command contains dangerous patterns"
        args = shlex.split(command)
        for arg in args[1:]:
            if ".." in arg or os.path.isabs(arg):
                return "Path traversal detected"
        return None

    def _set_limits(self) -> None:
        if resource is None:
            return
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
            mem = 256 * 1024 * 1024  # 256MB
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
            resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.warning("Failed to set resource limits", error=str(exc))

    def _truncate(self, text: str) -> tuple[str, bool]:
        encoded = text.encode("utf-8")
        if len(encoded) <= self.max_output_bytes:
            return text, False
        truncated = encoded[: self.max_output_bytes].decode("utf-8", "ignore")
        return truncated, True

    def execute(
        self,
        command: str,
        work_dir: Optional[str] = None,
        capture_output: bool = True,
        shell: bool = True,
    ) -> Dict[str, Any]:
        error = self._validate_command(command)
        if error:
            return {"success": False, "error": error}

        if work_dir:
            exec_dir_obj = None
            exec_dir = work_dir
            os.makedirs(exec_dir, exist_ok=True)
        else:
            exec_dir_obj = tempfile.TemporaryDirectory(dir=self.base_work_dir)
            exec_dir = exec_dir_obj.name

        env = {"PATH": os.environ.get("PATH", ""), "HOME": exec_dir}

        def preexec_fn():
            if shell:
                os.chdir(exec_dir)
            self._set_limits()

        try:
            process = subprocess.Popen(
                command if shell else shlex.split(command),
                shell=shell,
                cwd=exec_dir,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                text=True,
                env=env,
                preexec_fn=preexec_fn,
            )
            stdout, stderr = process.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "error": f"Command timed out after {self.timeout} seconds",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {self._command_name(command)}",
            }
        except Exception as exc:  # pragma: no cover
            return {"success": False, "error": str(exc)}
        finally:
            if exec_dir_obj is not None:
                try:
                    exec_dir_obj.cleanup()
                except Exception:  # pragma: no cover - best effort
                    pass

        note_parts = []
        if capture_output:
            stdout, t1 = self._truncate(stdout or "")
            stderr, t2 = self._truncate(stderr or "")
            if t1:
                note_parts.append("stdout")
            if t2:
                note_parts.append("stderr")
        result = {
            "success": process.returncode == 0,
            "command": command,
            "return_code": process.returncode,
            "stdout": stdout if capture_output else None,
            "stderr": stderr if capture_output else None,
            "working_dir": exec_dir,
        }
        if note_parts:
            result["note"] = (
                " and ".join(note_parts)
                + f" truncated to {self.max_output_bytes} bytes"
            )
        if process.returncode != 0:
            result.setdefault("error", stderr)
        return result
