"""Audit package exceptions.

Error codes: PARACLE-AUD-XXX
- PARACLE-AUD-001: Audit storage error
- PARACLE-AUD-002: Audit integrity error
- PARACLE-AUD-003: Audit export error
- PARACLE-AUD-004: Invalid audit event
- PARACLE-AUD-005: Audit retention error
"""

from typing import Any


class AuditError(Exception):
    """Base exception for audit operations.

    Attributes:
        code: Error code (PARACLE-AUD-XXX)
        message: Human-readable error message
        context: Additional context data
    """

    code: str = "PARACLE-AUD-000"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.context = context or {}

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class AuditStorageError(AuditError):
    """Raised when audit storage operations fail."""

    code: str = "PARACLE-AUD-001"

    def __init__(self, message: str, *, operation: str | None = None):
        super().__init__(
            message,
            context={"operation": operation},
        )
        self.operation = operation


class AuditIntegrityError(AuditError):
    """Raised when audit integrity verification fails."""

    code: str = "PARACLE-AUD-002"

    def __init__(
        self,
        message: str,
        *,
        event_id: str | None = None,
        expected_hash: str | None = None,
        actual_hash: str | None = None,
    ):
        super().__init__(
            message,
            context={
                "event_id": event_id,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
            },
        )
        self.event_id = event_id
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash


class AuditExportError(AuditError):
    """Raised when audit export operations fail."""

    code: str = "PARACLE-AUD-003"

    def __init__(
        self,
        message: str,
        *,
        export_format: str | None = None,
        output_path: str | None = None,
    ):
        super().__init__(
            message,
            context={
                "export_format": export_format,
                "output_path": output_path,
            },
        )
        self.export_format = export_format
        self.output_path = output_path


class InvalidAuditEventError(AuditError):
    """Raised when an audit event is invalid."""

    code: str = "PARACLE-AUD-004"

    def __init__(self, message: str, *, field: str | None = None):
        super().__init__(
            message,
            context={"field": field},
        )
        self.field = field


class AuditRetentionError(AuditError):
    """Raised when audit retention operations fail."""

    code: str = "PARACLE-AUD-005"

    def __init__(self, message: str, *, retention_days: int | None = None):
        super().__init__(
            message,
            context={"retention_days": retention_days},
        )
        self.retention_days = retention_days
