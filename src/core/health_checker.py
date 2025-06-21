from __future__ import annotations

import shutil
import psutil
from datetime import datetime
from typing import Any, Dict

from .api_client import APIClient


class HealthChecker:
    """Perform basic health checks for the application."""

    def __init__(self, api_client: APIClient) -> None:
        self.api_client = api_client

    async def _check_api(self) -> Dict[str, Any]:
        ok = await self.api_client.health_check()
        return {"ok": ok}

    def _check_memory(self) -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        return {
            "ok": mem.percent < 90,
            "total": mem.total,
            "used": mem.used,
            "percent": mem.percent,
        }

    def _check_disk_space(self) -> Dict[str, Any]:
        disk = shutil.disk_usage("/")
        percent_used = disk.used / disk.total * 100
        return {
            "ok": percent_used < 90,
            "total": disk.total,
            "used": disk.used,
            "percent": percent_used,
        }

    async def check_all(self) -> Dict[str, Any]:
        checks = {
            "api": await self._check_api(),
            "memory": self._check_memory(),
            "disk_space": self._check_disk_space(),
        }
        status = "healthy" if all(c["ok"] for c in checks.values()) else "unhealthy"
        return {
            "status": status,
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
