"""Paracle Logging - Enterprise-grade logging system.

This module provides a unified logging system following best practices:
- Python stdlib logging integration
- 12-Factor App compliance (stdout/stderr)
- Structured JSON logging
- Correlation ID support for distributed tracing
- ISO 42001 audit trail capabilities
- OpenTelemetry compatibility

Usage:
    from paracle_core.logging import get_logger, configure_logging

    # Configure once at startup
    configure_logging(level="INFO", json_format=True)

    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("Operation completed", extra={"user_id": "123"})

For audit logging:
    from paracle_core.logging import audit_log, AuditEvent

    audit_log(AuditEvent(
        action="agent.created",
        actor="user@example.com",
        resource="agent/code-reviewer",
        outcome="success",
    ))
"""

from paracle_core.logging.audit import (
    AuditCategory,
    AuditEvent,
    AuditLogger,
    AuditOutcome,
    AuditSeverity,
    audit_log,
    get_audit_logger,
)
from paracle_core.logging.config import (
    LogConfig,
    LogLevel,
    configure_logging,
    get_log_level,
    set_log_level,
)
from paracle_core.logging.context import (
    CorrelationContext,
    clear_correlation_id,
    correlation_id,
    get_correlation_id,
    set_correlation_id,
)
from paracle_core.logging.handlers import (
    AuditFileHandler,
    ParacleFileHandler,
    ParacleStreamHandler,
)
from paracle_core.logging.integration import (
    create_request_logging_middleware,
    log_agent_execution,
    log_workflow_execution,
    setup_eventbus_logging,
)
from paracle_core.logging.logger import ParacleLogger, get_logger
from paracle_core.logging.management import (
    AggregateQuery,
    LogEntry,
    LogManager,
    LogStats,
    SearchQuery,
    validate_config,
)
from paracle_core.logging.platform import (
    LogType,
    PlatformPaths,
    detect_platform,
    ensure_directories,
    get_info,
    get_log_path,
    get_platform_paths,
)
from paracle_core.logging.structured import JsonFormatter, StructuredFormatter

__all__ = [
    # Configuration
    "configure_logging",
    "get_log_level",
    "set_log_level",
    "LogLevel",
    "LogConfig",
    # Logger
    "get_logger",
    "ParacleLogger",
    # Context
    "CorrelationContext",
    "correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    "clear_correlation_id",
    # Formatters
    "StructuredFormatter",
    "JsonFormatter",
    # Audit
    "AuditEvent",
    "AuditLogger",
    "AuditCategory",
    "AuditOutcome",
    "AuditSeverity",
    "audit_log",
    "get_audit_logger",
    # Handlers
    "ParacleFileHandler",
    "ParacleStreamHandler",
    "AuditFileHandler",
    # Integration
    "create_request_logging_middleware",
    "log_agent_execution",
    "log_workflow_execution",
    "setup_eventbus_logging",
    # Platform paths (NEW)
    "LogType",
    "PlatformPaths",
    "detect_platform",
    "get_platform_paths",
    "get_log_path",
    "ensure_directories",
    "get_info",
    # Management (NEW)
    "LogManager",
    "LogEntry",
    "SearchQuery",
    "AggregateQuery",
    "LogStats",
    "validate_config",
]
