"""Prometheus metrics for Jan Assistant Pro."""

import asyncio
import functools
import time
from typing import Callable

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    start_http_server,
)

registry = CollectorRegistry()

# API metrics
api_calls = Counter("api_calls_total", "Total API calls", registry=registry)
api_errors = Counter("api_errors_total", "Total API errors", registry=registry)
api_latency = Histogram("api_latency_seconds", "API call latency", registry=registry)

# Tool metrics
tool_calls = Counter(
    "tool_calls_total", "Total tool invocations", ["tool"], registry=registry
)
tool_errors = Counter(
    "tool_errors_total", "Total tool errors", ["tool"], registry=registry
)

# Resource metrics
memory_usage = Gauge(
    "process_memory_bytes", "Process memory usage in bytes", registry=registry
)


def update_memory_usage() -> None:
    """Update memory usage gauge."""
    if psutil is None:
        return
    try:
        mem = psutil.Process().memory_info().rss
        memory_usage.set(mem)
    except Exception:
        pass


def export_metrics() -> bytes:
    """Return metrics in Prometheus text format."""
    update_memory_usage()
    return generate_latest(registry)


def start_metrics_server(port: int = 8000) -> None:
    """Start the Prometheus metrics HTTP server."""
    start_http_server(port, registry=registry)


def performance_timer(histogram: Histogram) -> Callable:
    """Decorator to time function execution with the given histogram."""

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    histogram.observe(time.perf_counter() - start)

            return functools.wraps(func)(async_wrapper)

        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                histogram.observe(time.perf_counter() - start)

        return functools.wraps(func)(wrapper)

    return decorator


def record_tool(tool_name: str) -> Callable:
    """Decorator to track tool usage and errors."""

    def decorator(func: Callable) -> Callable:
        counter = tool_calls.labels(tool=tool_name)
        error_counter = tool_errors.labels(tool=tool_name)

        def record_result(result):
            if isinstance(result, dict) and not result.get("success", True):
                error_counter.inc()

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                counter.inc()
                try:
                    result = await func(*args, **kwargs)
                except Exception:
                    error_counter.inc()
                    raise
                record_result(result)
                return result

            return functools.wraps(func)(async_wrapper)

        def wrapper(*args, **kwargs):
            counter.inc()
            try:
                result = func(*args, **kwargs)
            except Exception:
                error_counter.inc()
                raise
            record_result(result)
            return result

        return functools.wraps(func)(wrapper)

    return decorator
