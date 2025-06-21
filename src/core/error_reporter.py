from collections import Counter, deque
from typing import Any, Deque, Dict


class ErrorReporter:
    """Keep a rolling log of recent errors."""

    def __init__(self, max_entries: int = 50) -> None:
        self.max_entries = max_entries
        self._errors: Deque[Dict[str, str]] = deque(maxlen=max_entries)

    def record_error(self, exc: Exception) -> None:
        """Record an exception."""
        self._errors.append({"type": exc.__class__.__name__, "message": str(exc)})

    def generate_report(self) -> Dict[str, Any]:
        """Return aggregated error counts and recent messages."""
        counts = Counter(err["type"] for err in self._errors)
        return {
            "total_errors": len(self._errors),
            "counts": dict(counts),
            "recent": list(self._errors),
        }


_default_reporter = ErrorReporter()


def record_error(exc: Exception) -> None:
    """Record an error using the global reporter."""
    _default_reporter.record_error(exc)


def generate_report() -> Dict[str, Any]:
    """Generate a report from the global reporter."""
    return _default_reporter.generate_report()
