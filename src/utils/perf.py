"""
QuantDB Performance Instrumentation Utility.
Measures execution timing of database queries, service calls, analytics calculations,
and rendering pipelines without exposing secrets or flooding production logs.
"""

from contextlib import contextmanager
import logging
import os
import time
from typing import Any, Callable

logger = logging.getLogger("quantdb.perf")


def is_perf_debug_enabled() -> bool:
    """Returns True only when QUANTDB_PERF_DEBUG or DEBUG=1 is set."""
    val = os.getenv("QUANTDB_PERF_DEBUG", os.getenv("DEBUG", "0")).lower()
    return val in ("1", "true", "yes", "on")


@contextmanager
def perf_timer(label: str):
    """
    Context manager to time blocks of code when performance logging is active.
    Example:
        with perf_timer("market_data query"):
            df = repo.get_market_data(sec_id)
    """
    if not is_perf_debug_enabled():
        yield
        return

    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        logger.info(f"[PERF] {label}: {elapsed:.4f}s")
        print(f"[PERF] {label}: {elapsed:.4f}s")


def timed_operation(label: str):
    """Decorator to time a function when performance logging is enabled."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not is_perf_debug_enabled():
                return fn(*args, **kwargs)
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - t0
                print(f"[PERF] {label}: {elapsed:.4f}s")
        return wrapper
    return decorator
