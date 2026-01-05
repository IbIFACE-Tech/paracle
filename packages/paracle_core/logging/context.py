"""Correlation context for distributed tracing.

Provides correlation ID management for tracking requests across
distributed components and async operations.

Usage:
    from paracle_core.logging import correlation_id, get_correlation_id

    # In middleware or request handler
    with correlation_id():
        # All logs in this context will include the correlation ID
        logger.info("Processing request")

    # Or manually set
    set_correlation_id("req-12345")
    logger.info("Has correlation ID in logs")
"""

import contextvars
import uuid
from collections.abc import Generator
from contextlib import contextmanager

# Context variable for correlation ID (async-safe)
_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id",
    default=None,
)

# Context variable for additional context
_log_context: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "log_context",
    default=None,
)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID.

    Returns:
        A unique identifier string (UUID4 format)
    """
    return str(uuid.uuid4())


def get_correlation_id() -> str | None:
    """Get the current correlation ID.

    Returns:
        The correlation ID or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(cid: str | None) -> None:
    """Set the correlation ID for the current context.

    Args:
        cid: The correlation ID to set, or None to clear
    """
    _correlation_id.set(cid)


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    _correlation_id.set(None)


@contextmanager
def correlation_id(cid: str | None = None) -> Generator[str, None, None]:
    """Context manager for correlation ID scope.

    If no ID is provided, generates a new one.

    Args:
        cid: Optional correlation ID to use

    Yields:
        The correlation ID for this context

    Example:
        with correlation_id() as cid:
            logger.info("Request started")
            # All logs include the correlation ID
            process_request()
            logger.info("Request completed")
    """
    if cid is None:
        cid = generate_correlation_id()

    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)


def get_log_context() -> dict:
    """Get the current logging context.

    Returns:
        Dictionary of context values
    """
    ctx = _log_context.get()
    return ctx.copy() if ctx is not None else {}


def set_log_context(**kwargs) -> None:
    """Add values to the logging context.

    Args:
        **kwargs: Key-value pairs to add to context
    """
    current = _log_context.get() or {}
    _log_context.set({**current, **kwargs})


def clear_log_context() -> None:
    """Clear the logging context."""
    _log_context.set({})


@contextmanager
def log_context(**kwargs) -> Generator[dict, None, None]:
    """Context manager for temporary logging context.

    Args:
        **kwargs: Key-value pairs to add to context

    Yields:
        The full context dictionary

    Example:
        with log_context(user_id="123", agent="coder"):
            logger.info("Processing")  # Includes user_id and agent
    """
    current = _log_context.get()
    new_context = {**current, **kwargs}
    token = _log_context.set(new_context)
    try:
        yield new_context
    finally:
        _log_context.reset(token)


class CorrelationContext:
    """Class-based correlation context for more control.

    Example:
        ctx = CorrelationContext()
        ctx.set("request_id", "req-123")
        ctx.set("user_id", "user-456")

        with ctx:
            logger.info("Has all context")
    """

    def __init__(
        self,
        correlation_id: str | None = None,
        **initial_context,
    ):
        """Initialize correlation context.

        Args:
            correlation_id: Optional correlation ID
            **initial_context: Initial context values
        """
        self._correlation_id = correlation_id or generate_correlation_id()
        self._context = initial_context
        self._cid_token = None
        self._ctx_token = None

    @property
    def correlation_id(self) -> str:
        """Get the correlation ID."""
        return self._correlation_id

    def set(self, key: str, value) -> "CorrelationContext":
        """Add a value to the context.

        Args:
            key: Context key
            value: Context value

        Returns:
            Self for chaining
        """
        self._context[key] = value
        return self

    def get(self, key: str, default=None):
        """Get a value from the context.

        Args:
            key: Context key
            default: Default if not found

        Returns:
            The value or default
        """
        return self._context.get(key, default)

    def to_dict(self) -> dict:
        """Get all context as dictionary.

        Returns:
            Dictionary with correlation_id and all context
        """
        return {
            "correlation_id": self._correlation_id,
            **self._context,
        }

    def __enter__(self) -> "CorrelationContext":
        """Enter the context."""
        self._cid_token = _correlation_id.set(self._correlation_id)
        current = _log_context.get()
        self._ctx_token = _log_context.set({**current, **self._context})
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context."""
        if self._cid_token is not None:
            _correlation_id.reset(self._cid_token)
        if self._ctx_token is not None:
            _log_context.reset(self._ctx_token)
