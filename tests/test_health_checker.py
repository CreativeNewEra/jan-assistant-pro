import asyncio
import pytest

from src.core.health_checker import HealthChecker


class DummyClient:
    async def health_check(self):
        return True


@pytest.mark.asyncio
async def test_health_checker_success():
    checker = HealthChecker(DummyClient())
    result = await checker.check_all()
    assert result["status"] == "healthy"
    assert result["checks"]["api"]["ok"] is True
    assert "memory" in result["checks"]
    assert "disk_space" in result["checks"]
