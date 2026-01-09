"""Error registry for centralized error tracking and analytics.

This module provides centralized error collection, frequency analysis,
pattern detection, and error correlation capabilities.

Example:
    >>> from paracle_observability import ErrorRegistry
    >>>
    >>> registry = ErrorRegistry()
    >>>
    >>> # Record error
    >>> error = ValueError("Connection timeout")
    >>> registry.record_error(
    ...     error=error,
    ...     component="api_client",
    ...     context={"url": "https://api.example.com", "retry_count": 3}
    ... )
    >>>
    >>> # Query errors
    >>> recent_errors = registry.get_errors(limit=10)
    >>> api_errors = registry.get_errors_by_component("api_client")
    >>>
    >>> # Analytics
    >>> stats = registry.get_statistics()
    >>> print(f"Total errors: {stats['total_count']}")
    >>> print(f"Error rate: {stats['error_rate']} errors/min")
"""

import json
import time
import traceback
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Single error record.

    Attributes:
        id: Unique error identifier
        timestamp: When error occurred
        error_type: Exception class name
        error_code: Error code (e.g., PARACLE-CORE-001)
        message: Error message
        component: Component where error occurred
        severity: Error severity level
        context: Additional context
        stack_trace: Stack trace
        count: Number of occurrences (for deduplication)
        first_seen: First occurrence timestamp
        last_seen: Last occurrence timestamp
    """

    id: str
    timestamp: float
    error_type: str
    error_code: str | None
    message: str
    component: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    context: dict[str, Any] = field(default_factory=dict)
    stack_trace: str | None = None
    count: int = 1
    first_seen: float | None = None
    last_seen: float | None = None

    def __post_init__(self):
        """Initialize first/last seen timestamps."""
        if self.first_seen is None:
            self.first_seen = self.timestamp
        if self.last_seen is None:
            self.last_seen = self.timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class ErrorRegistry:
    """Centralized error tracking and analytics.

    Tracks errors across components, provides frequency analysis,
    pattern detection, and correlation.

    Attributes:
        errors: List of error records
        error_counts: Error counts by type
        component_errors: Errors by component
        error_patterns: Detected error patterns
        max_errors: Maximum errors to store
    """

    def __init__(self, max_errors: int = 10000):
        """Initialize error registry.

        Args:
            max_errors: Maximum errors to store (default: 10000)
        """
        self.max_errors = max_errors
        self.errors: list[ErrorRecord] = []
        self.error_counts: dict[str, int] = defaultdict(int)
        self.component_errors: dict[str, list[ErrorRecord]] = defaultdict(list)
        self.error_patterns: list[dict[str, Any]] = []
        self._error_index: dict[str, ErrorRecord] = {}  # For deduplication
        self._start_time = time.time()

    def _generate_error_id(self, error: Exception, component: str) -> str:
        """Generate unique error identifier for deduplication.

        Args:
            error: Exception instance
            component: Component name

        Returns:
            Error ID
        """
        error_type = type(error).__name__
        message = str(error)
        return f"{component}:{error_type}:{hash(message) % 1000000}"

    def _extract_error_code(self, error: Exception) -> str | None:
        """Extract error code from exception.

        Args:
            error: Exception instance

        Returns:
            Error code if available
        """
        if hasattr(error, "error_code"):
            return error.error_code
        return None

    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity.

        Args:
            error: Exception instance

        Returns:
            Severity level
        """
        # Critical errors
        if isinstance(error, (SystemExit, KeyboardInterrupt, MemoryError)):
            return ErrorSeverity.CRITICAL

        # Specific error types
        error_name = type(error).__name__.lower()
        if "timeout" in error_name or "connection" in error_name:
            return ErrorSeverity.WARNING

        # Default to ERROR
        return ErrorSeverity.ERROR

    def record_error(
        self,
        error: Exception,
        component: str,
        severity: ErrorSeverity | None = None,
        context: dict[str, Any] | None = None,
        include_traceback: bool = True,
    ) -> ErrorRecord:
        """Record an error.

        Args:
            error: Exception instance
            component: Component where error occurred
            severity: Optional severity override
            context: Additional context
            include_traceback: Include stack trace

        Returns:
            ErrorRecord instance
        """
        error_id = self._generate_error_id(error, component)
        timestamp = time.time()

        # Check for duplicate (deduplicate similar errors)
        if error_id in self._error_index:
            existing = self._error_index[error_id]
            existing.count += 1
            existing.last_seen = timestamp
            return existing

        # Create new record
        error_record = ErrorRecord(
            id=error_id,
            timestamp=timestamp,
            error_type=type(error).__name__,
            error_code=self._extract_error_code(error),
            message=str(error),
            component=component,
            severity=severity or self._determine_severity(error),
            context=context or {},
            stack_trace=(
                "".join(traceback.format_tb(error.__traceback__))
                if include_traceback and error.__traceback__
                else None
            ),
        )

        # Store record
        self.errors.append(error_record)
        self._error_index[error_id] = error_record
        self.error_counts[error_record.error_type] += 1
        self.component_errors[component].append(error_record)

        # Trim if needed
        if len(self.errors) > self.max_errors:
            removed = self.errors.pop(0)
            del self._error_index[removed.id]

        # Detect patterns
        self._detect_patterns()

        return error_record

    def _detect_patterns(self):
        """Detect error patterns (high frequency, cascading errors)."""
        # Pattern: High frequency errors (> 10 in last minute)
        one_minute_ago = time.time() - 60
        recent_errors = [e for e in self.errors if e.timestamp >= one_minute_ago]

        error_type_counts = defaultdict(int)
        for error in recent_errors:
            error_type_counts[error.error_type] += 1

        # Clear old patterns
        self.error_patterns = []

        # High frequency pattern
        for error_type, count in error_type_counts.items():
            if count >= 10:
                self.error_patterns.append(
                    {
                        "pattern_type": "high_frequency",
                        "error_type": error_type,
                        "count": count,
                        "time_window": "1_minute",
                        "detected_at": time.time(),
                    }
                )

        # Cascading errors pattern (multiple errors in same component)
        component_counts = defaultdict(int)
        for error in recent_errors:
            component_counts[error.component] += 1

        for component, count in component_counts.items():
            if count >= 5:
                self.error_patterns.append(
                    {
                        "pattern_type": "cascading",
                        "component": component,
                        "count": count,
                        "time_window": "1_minute",
                        "detected_at": time.time(),
                    }
                )

    def get_errors(
        self,
        limit: int | None = None,
        since: float | None = None,
        severity: ErrorSeverity | None = None,
        component: str | None = None,
    ) -> list[ErrorRecord]:
        """Get errors with optional filtering.

        Args:
            limit: Maximum number of errors
            since: Only errors after this timestamp
            severity: Filter by severity
            component: Filter by component

        Returns:
            List of error records
        """
        results = self.errors

        # Filter by timestamp
        if since:
            results = [e for e in results if e.timestamp >= since]

        # Filter by severity
        if severity:
            results = [e for e in results if e.severity == severity]

        # Filter by component
        if component:
            results = [e for e in results if e.component == component]

        # Sort by timestamp descending
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)

        # Limit
        if limit:
            results = results[:limit]

        return results

    def get_errors_by_component(self, component: str) -> list[ErrorRecord]:
        """Get all errors for a specific component.

        Args:
            component: Component name

        Returns:
            List of error records
        """
        return sorted(
            self.component_errors[component],
            key=lambda e: e.timestamp,
            reverse=True,
        )

    def get_errors_by_type(self, error_type: str) -> list[ErrorRecord]:
        """Get all errors of a specific type.

        Args:
            error_type: Error type name

        Returns:
            List of error records
        """
        return [e for e in self.errors if e.error_type == error_type]

    def get_error_count(
        self,
        since: float | None = None,
        component: str | None = None,
    ) -> int:
        """Get error count with optional filtering.

        Args:
            since: Only count errors after this timestamp
            component: Filter by component

        Returns:
            Error count
        """
        return len(self.get_errors(since=since, component=component))

    def get_statistics(self) -> dict[str, Any]:
        """Get error statistics.

        Returns:
            Statistics dictionary
        """
        uptime = time.time() - self._start_time

        # Recent errors (last hour)
        one_hour_ago = time.time() - 3600
        recent_errors = [e for e in self.errors if e.timestamp >= one_hour_ago]

        # Error rate (per minute)
        error_rate = (len(recent_errors) / 60) if uptime >= 60 else 0

        # Top error types
        top_errors = sorted(
            self.error_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Top components
        component_counts = {
            comp: len(errors) for comp, errors in self.component_errors.items()
        }
        top_components = sorted(
            component_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        # Severity breakdown
        severity_counts = defaultdict(int)
        for error in self.errors:
            severity_counts[error.severity.value] += 1

        return {
            "total_count": len(self.errors),
            "unique_errors": len(self._error_index),
            "uptime_seconds": uptime,
            "error_rate_per_minute": error_rate,
            "recent_errors_1h": len(recent_errors),
            "top_error_types": [{"type": t, "count": c} for t, c in top_errors],
            "top_components": [
                {"component": c, "count": cnt} for c, cnt in top_components
            ],
            "severity_breakdown": dict(severity_counts),
            "patterns_detected": len(self.error_patterns),
        }

    def get_patterns(self) -> list[dict[str, Any]]:
        """Get detected error patterns.

        Returns:
            List of pattern dictionaries
        """
        return self.error_patterns

    def search_errors(
        self,
        query: str,
        field: str = "message",
        case_sensitive: bool = False,
    ) -> list[ErrorRecord]:
        """Search errors by field.

        Args:
            query: Search query
            field: Field to search (message, component, error_type)
            case_sensitive: Case-sensitive search

        Returns:
            Matching error records
        """
        if not case_sensitive:
            query = query.lower()

        results = []
        for error in self.errors:
            value = getattr(error, field, "")
            if not case_sensitive:
                value = value.lower()

            if query in value:
                results.append(error)

        return sorted(results, key=lambda e: e.timestamp, reverse=True)

    def export_errors(
        self,
        format: str = "json",
        limit: int | None = None,
    ) -> str:
        """Export errors to format.

        Args:
            format: Export format (json)
            limit: Maximum errors to export

        Returns:
            Exported data as string
        """
        errors = self.get_errors(limit=limit)

        if format == "json":
            data = {
                "exported_at": datetime.now().isoformat(),
                "count": len(errors),
                "errors": [e.to_dict() for e in errors],
            }
            return json.dumps(data, indent=2)

        raise ValueError(f"Unsupported format: {format}")

    def clear(self):
        """Clear all error records."""
        self.errors.clear()
        self.error_counts.clear()
        self.component_errors.clear()
        self.error_patterns.clear()
        self._error_index.clear()
        self._start_time = time.time()


# Global error registry instance
_global_registry: ErrorRegistry | None = None


def get_error_registry() -> ErrorRegistry:
    """Get global error registry instance.

    Returns:
        ErrorRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ErrorRegistry()
    return _global_registry
