"""Structured logging formatters.

Provides formatters for structured logging output:
- StructuredFormatter: Human-readable structured format
- JsonFormatter: Machine-parseable JSON format
"""

import json
import logging
import socket
import traceback
from datetime import datetime, timezone
from typing import Any

from paracle_core.logging.context import get_correlation_id, get_log_context


class StructuredFormatter(logging.Formatter):
    """Human-readable structured log formatter.

    Output format:
        2024-01-02T10:30:00.123Z [INFO] [correlation_id] logger.name - Message {extra}

    Example:
        2024-01-02T10:30:00.123Z [INFO] [abc123] paracle.api - Request started {"method": "GET"}
    """

    def __init__(
        self,
        include_correlation_id: bool = True,
        include_timestamp: bool = True,
        datefmt: str | None = None,
    ):
        """Initialize formatter.

        Args:
            include_correlation_id: Include correlation ID in output
            include_timestamp: Include ISO timestamp
            datefmt: Date format string (default: ISO 8601)
        """
        super().__init__()
        self.include_correlation_id = include_correlation_id
        self.include_timestamp = include_timestamp
        self._datefmt = datefmt

    def format(self, record: logging.LogRecord) -> str:
        """Format log record.

        Args:
            record: The log record

        Returns:
            Formatted log string
        """
        parts = []

        # Timestamp (ISO 8601 with milliseconds)
        if self.include_timestamp:
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            timestamp = (
                dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond/1000):03d}Z"
            )
            parts.append(timestamp)

        # Level
        parts.append(f"[{record.levelname}]")

        # Correlation ID
        if self.include_correlation_id:
            cid = get_correlation_id()
            if cid:
                parts.append(f"[{cid[:8]}]")  # Truncate for readability

        # Logger name
        parts.append(record.name)
        parts.append("-")

        # Message
        parts.append(record.getMessage())

        # Extra fields (from extra={} and context)
        extra = self._get_extra(record)
        if extra:
            parts.append(json.dumps(extra, default=str))

        # Exception
        if record.exc_info:
            parts.append("\n" + self.formatException(record.exc_info))

        return " ".join(parts)

    def _get_extra(self, record: logging.LogRecord) -> dict:
        """Extract extra fields from record.

        Args:
            record: The log record

        Returns:
            Dictionary of extra fields
        """
        # Standard LogRecord attributes to exclude
        standard_attrs = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "message",
            "asctime",
        }

        extra = {}

        # Add record extras
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                extra[key] = value

        # Add context
        context = get_log_context()
        extra.update(context)

        return extra


class JsonFormatter(logging.Formatter):
    """JSON structured log formatter.

    Output format:
        {"timestamp": "...", "level": "INFO", "logger": "...", "message": "...", ...}

    Suitable for log aggregation systems (ELK, Loki, CloudWatch, etc.)
    """

    # Standard fields always included
    STANDARD_FIELDS = {
        "timestamp",
        "level",
        "logger",
        "message",
        "correlation_id",
    }

    def __init__(
        self,
        include_correlation_id: bool = True,
        include_timestamp: bool = True,
        include_hostname: bool = False,
        include_process: bool = False,
        include_thread: bool = False,
        indent: int | None = None,
    ):
        """Initialize JSON formatter.

        Args:
            include_correlation_id: Include correlation ID
            include_timestamp: Include ISO timestamp
            include_hostname: Include hostname for distributed systems
            include_process: Include process ID
            include_thread: Include thread name
            indent: JSON indent (None for compact)
        """
        super().__init__()
        self.include_correlation_id = include_correlation_id
        self.include_timestamp = include_timestamp
        self.include_hostname = include_hostname
        self.include_process = include_process
        self.include_thread = include_thread
        self.indent = indent
        self._hostname = socket.gethostname() if include_hostname else None

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record

        Returns:
            JSON string
        """
        log_dict = self._build_log_dict(record)
        return json.dumps(log_dict, default=self._json_serializer, indent=self.indent)

    def _build_log_dict(self, record: logging.LogRecord) -> dict[str, Any]:
        """Build log dictionary from record.

        Args:
            record: The log record

        Returns:
            Dictionary for JSON serialization
        """
        log_dict = {}

        # Timestamp (ISO 8601)
        if self.include_timestamp:
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            log_dict["timestamp"] = dt.isoformat()

        # Standard fields
        log_dict["level"] = record.levelname
        log_dict["logger"] = record.name
        log_dict["message"] = record.getMessage()

        # Correlation ID
        if self.include_correlation_id:
            cid = get_correlation_id()
            if cid:
                log_dict["correlation_id"] = cid

        # Optional fields
        if self.include_hostname and self._hostname:
            log_dict["hostname"] = self._hostname

        if self.include_process:
            log_dict["process_id"] = record.process
            log_dict["process_name"] = record.processName

        if self.include_thread:
            log_dict["thread_id"] = record.thread
            log_dict["thread_name"] = record.threadName

        # Location info
        log_dict["location"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Extra fields from extra={}
        extra = self._get_extra(record)
        if extra:
            log_dict["extra"] = extra

        # Context
        context = get_log_context()
        if context:
            log_dict["context"] = context

        # Exception
        if record.exc_info:
            log_dict["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return log_dict

    def _get_extra(self, record: logging.LogRecord) -> dict:
        """Extract extra fields from record.

        Args:
            record: The log record

        Returns:
            Dictionary of extra fields
        """
        standard_attrs = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "message",
            "asctime",
        }

        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                extra[key] = value

        return extra

    def _json_serializer(self, obj: Any) -> Any:
        """JSON serializer for non-standard types.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)
