"""Reusable utilities for the OmniParser-RAG project."""

from collections.abc import Callable
import functools
import logging
import time
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def trace(func: F) -> F:
    """Decorator that logs method entry, exit, arguments, and elapsed time.

    Messages are emitted at DEBUG level, so they remain silent unless
    ``LOG_LEVEL`` is explicitly set to ``DEBUG``.

    For bound methods the ``self`` / ``cls`` argument is automatically
    omitted from the logged arguments to reduce noise.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)

        # Skip 'self' or 'cls' for bound methods
        display_args = args[1:] if args and hasattr(args[0], func.__name__) else args
        formatted = ", ".join(
            [repr(a) for a in display_args] + [f"{k}={v!r}" for k, v in kwargs.items()]
        )

        logger.debug("→ %s(%s)", func.__qualname__, formatted)

        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception:
            elapsed = time.perf_counter() - start
            logger.debug("✗ %s raised after %.3fs", func.__qualname__, elapsed)
            raise

        elapsed = time.perf_counter() - start
        logger.debug("← %s [%.3fs]", func.__qualname__, elapsed)
        return result

    return wrapper  # type: ignore[return-value]
