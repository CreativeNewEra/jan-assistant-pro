from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine


class AsyncGUIBridge:
    """Bridge to run async tasks from a GUI thread."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_async(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Future:
        """Schedule ``coro`` to run in the background event loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future

    def shutdown(self) -> None:
        """Stop the event loop and wait for the thread to exit."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=5)
