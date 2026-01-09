"""Paracle Audit Package.

This package provides audit trail functionality for ISO 42001 compliance:
- Audit Events: Record all agent actions and governance decisions
- Audit Trail: Tamper-evident audit log storage
- Integrity Verification: Hash chain verification
- Export: Export audit data for compliance reporting

Example:
    >>> from paracle_audit import AuditTrail, AuditEvent, AuditEventType
    >>> trail = AuditTrail()
    >>> event = trail.record(
    ...     event_type=AuditEventType.AGENT_ACTION,
    ...     actor="coder",
    ...     action="write_file",
    ...     target="/app/main.py",
    ...     outcome="success",
    ... )
    >>> print(event.event_id)
"""

from .events import AuditEvent, AuditEventType, AuditOutcome
from .exceptions import (
    AuditError,
    AuditExportError,
    AuditIntegrityError,
    AuditStorageError,
)
from .export import AuditExporter, ExportFormat
from .integrity import IntegrityVerifier
from .storage import AuditStorage, SQLiteAuditStorage
from .trail import AuditTrail

__all__ = [
    # Events
    "AuditEvent",
    "AuditEventType",
    "AuditOutcome",
    # Trail
    "AuditTrail",
    # Storage
    "AuditStorage",
    "SQLiteAuditStorage",
    # Integrity
    "IntegrityVerifier",
    # Export
    "AuditExporter",
    "ExportFormat",
    # Exceptions
    "AuditError",
    "AuditStorageError",
    "AuditIntegrityError",
    "AuditExportError",
]

__version__ = "1.0.1"
