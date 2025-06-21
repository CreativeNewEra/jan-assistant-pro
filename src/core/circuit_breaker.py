from __future__ import annotations

import time


class CircuitBreaker:
    """Simple circuit breaker for API calls."""

    OPEN = "open"
    CLOSED = "closed"
    HALF_OPEN = "half_open"

    def __init__(self, fail_max: int = 3, reset_timeout: int = 60) -> None:
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.state = self.CLOSED
        self._opened_at = 0.0

    def allow(self) -> bool:
        """Return True if a call is allowed."""
        if self.state == self.OPEN:
            if time.time() - self._opened_at >= self.reset_timeout:
                self.state = self.HALF_OPEN
            else:
                return False
        return True

    def _open(self) -> None:
        self.state = self.OPEN
        self._opened_at = time.time()
        self.failure_count = self.fail_max

    def _close(self) -> None:
        self.state = self.CLOSED
        self.failure_count = 0
        self._opened_at = 0.0

    def record_success(self) -> None:
        """Record a successful call."""
        self._close()

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        if self.state == self.HALF_OPEN or self.failure_count >= self.fail_max:
            self._open()

    def after_call(self, success: bool) -> None:
        """Update breaker state based on call result."""
        if success:
            self.record_success()
        else:
            self.record_failure()
