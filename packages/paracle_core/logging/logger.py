"""Paracle logger implementation.

Provides the main logger interface for the framework.
"""

import logging

from paracle_core.logging.context import get_correlation_id, get_log_context


class ParacleLogger(logging.Logger):
    """Extended logger with Paracle-specific features.

    Features:
    - Automatic correlation ID injection
    - Context-aware logging
    - Structured extra fields
    - Convenience methods for common patterns
    """

    def __init__(self, name: str, level: int = logging.NOTSET):
        """Initialize Paracle logger.

        Args:
            name: Logger name
            level: Log level
        """
        super().__init__(name, level)

    def _log(
        self,
        level: int,
        msg: object,
        args,
        exc_info=None,
        extra=None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        """Log with automatic context injection.

        Args:
            level: Log level
            msg: Log message
            args: Message format args
            exc_info: Exception info
            extra: Extra fields
            stack_info: Include stack info
            stacklevel: Stack level for caller info
        """
        # Merge extra with context
        merged_extra = {}

        # Add log context
        context = get_log_context()
        merged_extra.update(context)

        # Add provided extra
        if extra:
            merged_extra.update(extra)

        # Add correlation ID if not present
        cid = get_correlation_id()
        if cid and "correlation_id" not in merged_extra:
            merged_extra["correlation_id"] = cid

        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=merged_extra if merged_extra else None,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
        )

    def log_event(
        self,
        event_type: str,
        message: str,
        level: int = logging.INFO,
        **kwargs,
    ) -> None:
        """Log a structured event.

        Args:
            event_type: Type of event (e.g., "agent.started")
            message: Human-readable message
            level: Log level
            **kwargs: Additional event data
        """
        extra = {"event_type": event_type, **kwargs}
        self.log(level, message, extra=extra)

    def log_operation(
        self,
        operation: str,
        status: str = "started",
        duration_ms: float | None = None,
        **kwargs,
    ) -> None:
        """Log an operation status.

        Args:
            operation: Operation name
            status: Status (started, completed, failed)
            duration_ms: Duration in milliseconds
            **kwargs: Additional data
        """
        extra = {
            "operation": operation,
            "status": status,
            **kwargs,
        }
        if duration_ms is not None:
            extra["duration_ms"] = duration_ms

        level = logging.INFO
        if status == "failed":
            level = logging.ERROR

        self.log(level, f"Operation {operation}: {status}", extra=extra)

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs,
    ) -> None:
        """Log an HTTP request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration
            **kwargs: Additional data
        """
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING

        extra = {
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": duration_ms,
            **kwargs,
        }

        self.log(
            level, f"{method} {path} {status_code} ({duration_ms:.2f}ms)", extra=extra
        )

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        status: str = "started",
        **kwargs,
    ) -> None:
        """Log an agent action.

        Args:
            agent_name: Name of the agent
            action: Action being performed
            status: Action status
            **kwargs: Additional data
        """
        extra = {
            "agent_name": agent_name,
            "agent_action": action,
            "status": status,
            **kwargs,
        }

        level = logging.INFO
        if status == "failed":
            level = logging.ERROR

        self.log(level, f"Agent {agent_name}: {action} ({status})", extra=extra)


# Logger cache
_loggers: dict[str, ParacleLogger] = {}


def get_logger(name: str | None = None) -> ParacleLogger:
    """Get or create a Paracle logger.

    Args:
        name: Logger name (default: "paracle")

    Returns:
        ParacleLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Hello", extra={"user_id": "123"})
    """
    if name is None:
        name = "paracle"

    # Ensure name is under paracle namespace
    if not name.startswith("paracle"):
        name = f"paracle.{name}"

    if name in _loggers:
        return _loggers[name]

    # Register our logger class
    old_class = logging.getLoggerClass()
    logging.setLoggerClass(ParacleLogger)

    try:
        logger = logging.getLogger(name)
        # Ensure it's a ParacleLogger
        if not isinstance(logger, ParacleLogger):
            # Create new logger
            logger = ParacleLogger(name)
            logging.Logger.manager.loggerDict[name] = logger
    finally:
        logging.setLoggerClass(old_class)

    _loggers[name] = logger
    return logger


def log_with_context(
    level: int,
    message: str,
    logger_name: str | None = None,
    **context,
) -> None:
    """Convenience function for logging with context.

    Args:
        level: Log level
        message: Log message
        logger_name: Optional logger name
        **context: Context to include in log
    """
    logger = get_logger(logger_name)
    logger.log(level, message, extra=context)
