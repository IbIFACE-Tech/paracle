"""Logging configuration module.

Provides centralized logging configuration following best practices:
- Environment-driven configuration
- Multiple output targets (stdout, file, audit)
- Log level management
- Format selection (text, JSON)
- Platform-specific paths (Windows, Linux, macOS, Docker)
"""

import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from paracle_core.logging.platform import get_log_path


class LogLevel(str, Enum):
    """Standard log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def to_logging_level(self) -> int:
        """Convert to Python logging level."""
        return getattr(logging, self.value)


class LogConfig(BaseModel):
    """Logging configuration model."""

    # Core settings
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Default log level",
    )
    json_format: bool = Field(
        default=False,
        description="Use JSON structured logging",
    )

    # Output destinations
    log_to_stdout: bool = Field(
        default=True,
        description="Log to stdout (12-Factor App compliance)",
    )
    log_to_file: bool = Field(
        default=False,
        description="Also log to file",
    )
    log_file_path: Path | None = Field(
        default=None,
        description="Path to log file (if log_to_file=True)",
    )
    use_platform_paths: bool = Field(
        default=True,
        description="Use platform-specific paths for framework logs",
    )

    # Rotation settings
    max_bytes: int = Field(
        default=10_485_760,  # 10MB
        description="Max log file size before rotation",
    )
    backup_count: int = Field(
        default=5,
        description="Number of backup files to keep",
    )

    # Audit settings
    audit_enabled: bool = Field(
        default=True,
        description="Enable audit logging for ISO 42001",
    )
    audit_file_path: Path | None = Field(
        default=None,
        description="Path to audit log file",
    )

    # Context settings
    include_correlation_id: bool = Field(
        default=True,
        description="Include correlation ID in logs",
    )
    include_timestamp: bool = Field(
        default=True,
        description="Include ISO timestamp",
    )
    include_hostname: bool = Field(
        default=False,
        description="Include hostname for distributed systems",
    )

    # Performance settings
    async_logging: bool = Field(
        default=False,
        description="Use async logging for high throughput",
    )

    @classmethod
    def from_env(cls) -> "LogConfig":
        """Load configuration from environment variables.

        Environment variables:
            PARACLE_LOG_LEVEL: Log level (DEBUG, INFO, etc.)
            PARACLE_LOG_JSON: Use JSON format (true/false)
            PARACLE_LOG_FILE: Path to log file
            PARACLE_LOG_AUDIT: Enable audit logging (true/false)
            PARACLE_LOG_AUDIT_FILE: Path to audit log file
            PARACLE_USE_PLATFORM_PATHS: Use platform paths (true/false)
        """
        level_str = os.getenv("PARACLE_LOG_LEVEL", "INFO").upper()
        try:
            level = LogLevel(level_str)
        except ValueError:
            level = LogLevel.INFO

        json_fmt = os.getenv("PARACLE_LOG_JSON", "false").lower() == "true"
        log_file = os.getenv("PARACLE_LOG_FILE")
        audit_enabled = os.getenv("PARACLE_LOG_AUDIT", "true").lower() == "true"
        audit_file = os.getenv("PARACLE_LOG_AUDIT_FILE")
        use_platform = os.getenv("PARACLE_USE_PLATFORM_PATHS", "true").lower() == "true"

        # Use platform-specific paths if enabled and no explicit path
        if use_platform and log_file is None:
            log_file_path = get_log_path("main")
        else:
            log_file_path = Path(log_file) if log_file else None

        if use_platform and audit_file is None:
            audit_file_path = get_log_path("audit")
        else:
            audit_file_path = Path(audit_file) if audit_file else None

        return cls(
            level=level,
            json_format=json_fmt,
            log_to_file=log_file_path is not None,
            log_file_path=log_file_path,
            audit_enabled=audit_enabled,
            audit_file_path=audit_file_path,
            use_platform_paths=use_platform,
        )


# Global configuration instance
_config: LogConfig | None = None
_configured: bool = False


def get_config() -> LogConfig:
    """Get current logging configuration."""
    global _config
    if _config is None:
        _config = LogConfig.from_env()
    return _config


def configure_logging(
    level: str | LogLevel = LogLevel.INFO,
    json_format: bool = False,
    log_to_file: bool = False,
    log_file_path: str | Path | None = None,
    audit_enabled: bool = True,
    audit_file_path: str | Path | None = None,
    force: bool = False,
    **kwargs: Any,
) -> LogConfig:
    """Configure the logging system.

    This should be called once at application startup.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON structured logging
        log_to_file: Also log to file
        log_file_path: Path to log file
        audit_enabled: Enable audit logging
        audit_file_path: Path to audit log file
        force: Force reconfiguration even if already configured
        **kwargs: Additional configuration options

    Returns:
        The LogConfig instance

    Example:
        configure_logging(level="DEBUG", json_format=True)
    """
    global _config, _configured

    if _configured and not force:
        return get_config()

    # Convert string level to enum
    if isinstance(level, str):
        try:
            level = LogLevel(level.upper())
        except ValueError:
            level = LogLevel.INFO

    # Convert paths
    if log_file_path and isinstance(log_file_path, str):
        log_file_path = Path(log_file_path)
    if audit_file_path and isinstance(audit_file_path, str):
        audit_file_path = Path(audit_file_path)

    _config = LogConfig(
        level=level,
        json_format=json_format,
        log_to_file=log_to_file,
        log_file_path=log_file_path,
        audit_enabled=audit_enabled,
        audit_file_path=audit_file_path,
        **kwargs,
    )

    # Apply configuration to Python logging
    _apply_config(_config)
    _configured = True

    return _config


def _apply_config(config: LogConfig) -> None:
    """Apply configuration to Python logging system."""
    from paracle_core.logging.handlers import ParacleFileHandler, ParacleStreamHandler
    from paracle_core.logging.structured import JsonFormatter, StructuredFormatter

    # Get root logger for paracle
    root_logger = logging.getLogger("paracle")
    root_logger.setLevel(config.level.to_logging_level())

    # Remove existing handlers
    root_logger.handlers.clear()

    # Select formatter
    if config.json_format:
        formatter = JsonFormatter(
            include_correlation_id=config.include_correlation_id,
            include_timestamp=config.include_timestamp,
            include_hostname=config.include_hostname,
        )
    else:
        formatter = StructuredFormatter(
            include_correlation_id=config.include_correlation_id,
            include_timestamp=config.include_timestamp,
        )

    # Add stdout handler (12-Factor App compliance)
    if config.log_to_stdout:
        stream_handler = ParacleStreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(config.level.to_logging_level())
        root_logger.addHandler(stream_handler)

    # Add file handler if configured
    if config.log_to_file and config.log_file_path:
        config.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = ParacleFileHandler(
            filename=str(config.log_file_path),
            max_bytes=config.max_bytes,
            backup_count=config.backup_count,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(config.level.to_logging_level())
        root_logger.addHandler(file_handler)

    # Propagate to child loggers
    root_logger.propagate = False


def get_log_level() -> LogLevel:
    """Get current log level."""
    return get_config().level


def set_log_level(level: str | LogLevel) -> None:
    """Dynamically change log level.

    Args:
        level: New log level
    """
    global _config

    if isinstance(level, str):
        level = LogLevel(level.upper())

    if _config:
        _config.level = level

    # Update all paracle loggers
    root_logger = logging.getLogger("paracle")
    root_logger.setLevel(level.to_logging_level())

    for handler in root_logger.handlers:
        handler.setLevel(level.to_logging_level())
