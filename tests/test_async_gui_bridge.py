import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from src.gui.async_bridge import AsyncGUIBridge


def test_run_async_returns_result():
    bridge = AsyncGUIBridge()

    async def coro():
        return 42

    fut = bridge.run_async(coro())
    result = fut.result(timeout=1)
    assert result == 42

    bridge.shutdown()
    assert not bridge.thread.is_alive()


def test_run_async_propagates_exception():
    bridge = AsyncGUIBridge()

    async def bad():
        raise ValueError("boom")

    fut = bridge.run_async(bad())
    with pytest.raises(ValueError):
        fut.result(timeout=1)

    bridge.shutdown()
