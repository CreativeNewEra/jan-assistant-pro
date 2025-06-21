import logging
import time
import uuid


class RequestContext:
    """Context manager for request-scoped logging with correlation IDs."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.request_id = str(uuid.uuid4())
        self.start_time = time.time()

    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message with correlation ID and duration."""
        duration_ms = (time.time() - self.start_time) * 1000
        extra = {
            "extra_fields": {
                "request_id": self.request_id,
                "duration_ms": duration_ms,
                **kwargs,
            }
        }
        self.logger.log(
            getattr(logging, level.upper(), logging.INFO), message, extra=extra
        )
