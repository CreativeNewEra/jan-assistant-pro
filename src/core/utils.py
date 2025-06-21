import threading
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Iterator


@contextmanager
def thread_safe(lock: threading.Lock) -> Iterator[None]:
    """Acquire ``lock`` for the duration of the context."""
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def validate_input(rules: Dict[str, Any]):
    """Validate arguments (both positional and keyword) against provided rules."""
    import inspect

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the function's signature
            signature = inspect.signature(func)
            # Bind the provided arguments to the function's parameters
            bound_arguments = signature.bind(*args, **kwargs)
            bound_arguments.apply_defaults()

            # Validate each argument against the rules
            for param, rule in rules.items():
                if param in bound_arguments.arguments:
                    value = bound_arguments.arguments[param]
                    if "max_length" in rule and len(str(value)) > rule["max_length"]:
                        raise ValueError(f"{param} exceeds max length")
                    if "pattern" in rule and not rule["pattern"].match(str(value)):
                        raise ValueError(f"{param} has invalid format")
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["thread_safe", "validate_input"]
