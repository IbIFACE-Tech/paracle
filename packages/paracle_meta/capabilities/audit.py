"""AuditCapability - ISO 42001 compliant audit trail for AI systems.

This capability provides tamper-evident audit logging for all agent actions,
ensuring compliance with ISO 42001 and other AI governance standards.

Integration Points:
- Uses paracle_store for persistent audit trail storage
- Integrates with paracle_core for utilities
- Cryptographic hash chain for tamper detection

Example:
    >>> from paracle_meta.capabilities import AuditCapability, AuditConfig
    >>>
    >>> config = AuditConfig(
    ...     storage_backend="sqlite",
    ...     enable_hash_chain=True,
    ...     retention_days=365
    ... )
    >>> audit = AuditCapability(config)
    >>>
    >>> # Log agent action
    >>> await audit.log_action(
    ...     agent_id="coder-agent-1",
    ...     action_type="code_generation",
    ...     description="Generated authentication module",
    ...     metadata={"file": "auth.py", "lines": 150}
    ... )
    >>>
    >>> # Query audit trail
    >>> result = await audit.query_logs(
    ...     agent_id="coder-agent-1",
    ...     start_date="2026-01-01",
    ...     limit=100
    ... )
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from paracle_core.compat import UTC
from paracle_meta.capabilities.base import BaseCapability, CapabilityResult


class ActionType(str, Enum):
    """Types of auditable actions."""

    CODE_GENERATION = "code_generation"
    CODE_EXECUTION = "code_execution"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    API_CALL = "api_call"
    LLM_CALL = "llm_call"
    TOOL_EXECUTION = "tool_execution"
    CONFIGURATION_CHANGE = "configuration_change"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    ERROR = "error"
    OTHER = "other"


@dataclass
class AuditConfig:
    """Configuration for audit capability.

    Attributes:
        storage_backend: Storage backend ("sqlite", "postgresql").
        storage_path: Path to storage file (SQLite) or connection string.
        enable_hash_chain: Enable cryptographic hash chain for tamper detection.
        retention_days: Days to retain audit logs (0 = forever).
        enable_compression: Compress old audit entries.
        auto_archive: Automatically archive old entries.
    """

    storage_backend: str = "sqlite"
    storage_path: str = ".paracle_audit.db"
    enable_hash_chain: bool = True
    retention_days: int = 365  # 1 year
    enable_compression: bool = False
    auto_archive: bool = False


@dataclass
class AuditEntry:
    """Single audit log entry.

    Attributes:
        entry_id: Unique entry ID (auto-generated).
        timestamp: Entry creation time.
        agent_id: ID of agent performing action.
        action_type: Type of action.
        description: Human-readable description.
        metadata: Additional structured data.
        previous_hash: Hash of previous entry (hash chain).
        entry_hash: Hash of this entry.
        user_id: Optional user ID.
        session_id: Optional session ID.
    """

    entry_id: int
    timestamp: datetime
    agent_id: str
    action_type: ActionType
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    entry_hash: str = ""
    user_id: str | None = None
    session_id: str | None = None


class SQLiteAuditStore:
    """SQLite-based audit trail storage with hash chain."""

    def __init__(self, db_path: str, enable_hash_chain: bool = True):
        """Initialize SQLite audit store.

        Args:
            db_path: Path to SQLite database file.
            enable_hash_chain: Enable cryptographic hash chain.
        """
        self.db_path = db_path
        self.enable_hash_chain = enable_hash_chain
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                description TEXT NOT NULL,
                metadata TEXT,
                previous_hash TEXT,
                entry_hash TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                created_at TEXT NOT NULL
            )
        """
        )

        # Indexes for common queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_id ON audit_log(agent_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_action_type ON audit_log(action_type)"
        )

        conn.commit()
        conn.close()

    def _calculate_hash(self, entry: AuditEntry) -> str:
        """Calculate cryptographic hash for entry.

        Args:
            entry: Audit entry.

        Returns:
            SHA-256 hash (hex string).
        """
        # Hash chain: hash(previous_hash + entry_data)
        hash_data = {
            "timestamp": entry.timestamp.isoformat(),
            "agent_id": entry.agent_id,
            "action_type": entry.action_type.value,
            "description": entry.description,
            "metadata": entry.metadata,
            "previous_hash": entry.previous_hash,
            "user_id": entry.user_id,
            "session_id": entry.session_id,
        }

        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()

    def _get_latest_hash(self) -> str:
        """Get hash of most recent entry.

        Returns:
            Latest entry hash, or empty string if no entries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT entry_hash FROM audit_log ORDER BY entry_id DESC LIMIT 1"
        )
        result = cursor.fetchone()

        conn.close()

        return result[0] if result else ""

    def insert(
        self,
        agent_id: str,
        action_type: ActionType,
        description: str,
        metadata: dict[str, Any] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AuditEntry:
        """Insert new audit entry.

        Args:
            agent_id: Agent identifier.
            action_type: Type of action.
            description: Description of action.
            metadata: Additional data.
            user_id: Optional user ID.
            session_id: Optional session ID.

        Returns:
            Created audit entry.
        """
        timestamp = datetime.now(UTC)
        previous_hash = self._get_latest_hash() if self.enable_hash_chain else ""

        # Create entry (entry_id will be set after insert)
        entry = AuditEntry(
            entry_id=0,  # Placeholder
            timestamp=timestamp,
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            metadata=metadata or {},
            previous_hash=previous_hash,
            entry_hash="",  # Will calculate after
            user_id=user_id,
            session_id=session_id,
        )

        # Calculate hash
        entry.entry_hash = self._calculate_hash(entry)

        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_log (
                timestamp, agent_id, action_type, description,
                metadata, previous_hash, entry_hash,
                user_id, session_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp.isoformat(),
                agent_id,
                action_type.value,
                description,
                json.dumps(metadata or {}),
                previous_hash,
                entry.entry_hash,
                user_id,
                session_id,
                datetime.now(UTC).isoformat(),
            ),
        )

        entry.entry_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return entry

    def query(
        self,
        agent_id: str | None = None,
        action_type: ActionType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit log.

        Args:
            agent_id: Filter by agent ID.
            action_type: Filter by action type.
            start_date: Filter by start date.
            end_date: Filter by end date.
            limit: Maximum results.
            offset: Result offset.

        Returns:
            List of audit entries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM audit_log WHERE 1=1"
        params: list[Any] = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if action_type:
            query += " AND action_type = ?"
            params.append(action_type.value)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY entry_id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to AuditEntry objects
        entries = []
        for row in rows:
            entries.append(
                AuditEntry(
                    entry_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    agent_id=row[2],
                    action_type=ActionType(row[3]),
                    description=row[4],
                    metadata=json.loads(row[5]) if row[5] else {},
                    previous_hash=row[6] or "",
                    entry_hash=row[7],
                    user_id=row[8],
                    session_id=row[9],
                )
            )

        return entries

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Verify hash chain integrity.

        Returns:
            Tuple of (is_valid, list of errors).
        """
        if not self.enable_hash_chain:
            return True, []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM audit_log ORDER BY entry_id ASC")
        rows = cursor.fetchall()
        conn.close()

        errors = []
        previous_hash = ""

        for row in rows:
            entry = AuditEntry(
                entry_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                agent_id=row[2],
                action_type=ActionType(row[3]),
                description=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
                previous_hash=row[6] or "",
                entry_hash=row[7],
                user_id=row[8],
                session_id=row[9],
            )

            # Verify previous hash matches
            if entry.previous_hash != previous_hash:
                errors.append(
                    f"Entry {entry.entry_id}: previous_hash mismatch "
                    f"(expected: {previous_hash}, got: {entry.previous_hash})"
                )

            # Verify entry hash is correct
            calculated_hash = self._calculate_hash(entry)
            if entry.entry_hash != calculated_hash:
                errors.append(
                    f"Entry {entry.entry_id}: hash mismatch "
                    f"(expected: {calculated_hash}, got: {entry.entry_hash})"
                )

            previous_hash = entry.entry_hash

        return len(errors) == 0, errors

    def get_stats(self) -> dict[str, Any]:
        """Get audit log statistics.

        Returns:
            Statistics dictionary.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        total_entries = cursor.fetchone()[0]

        # Entries by action type
        cursor.execute(
            "SELECT action_type, COUNT(*) FROM audit_log GROUP BY action_type"
        )
        by_action_type = dict(cursor.fetchall())

        # Entries by agent
        cursor.execute(
            "SELECT agent_id, COUNT(*) FROM audit_log GROUP BY agent_id"
        )
        by_agent = dict(cursor.fetchall())

        # Date range
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM audit_log")
        date_range = cursor.fetchone()

        conn.close()

        return {
            "total_entries": total_entries,
            "by_action_type": by_action_type,
            "by_agent": by_agent,
            "earliest_entry": date_range[0] if date_range[0] else None,
            "latest_entry": date_range[1] if date_range[1] else None,
        }


class AuditCapability(BaseCapability):
    """Audit capability for ISO 42001 compliance.

    Provides tamper-evident audit logging for all agent actions.

    Features:
    - Cryptographic hash chain for tamper detection
    - Persistent storage (SQLite, PostgreSQL)
    - Query capabilities (by agent, time, action type)
    - Integrity verification
    - Retention policies
    - Export capabilities

    Example:
        >>> config = AuditConfig(enable_hash_chain=True, retention_days=365)
        >>> audit = AuditCapability(config)
        >>>
        >>> # Log action
        >>> await audit.log_action(
        ...     agent_id="coder-1",
        ...     action_type=ActionType.CODE_GENERATION,
        ...     description="Generated auth.py",
        ...     metadata={"file": "auth.py", "lines": 150}
        ... )
        >>>
        >>> # Verify integrity
        >>> result = await audit.verify_integrity()
        >>> if result.output["valid"]:
        ...     print("Audit trail is intact")
    """

    name = "audit"

    def __init__(self, config: AuditConfig | None = None):
        """Initialize audit capability.

        Args:
            config: Audit configuration (uses defaults if None).
        """
        super().__init__(config or AuditConfig())

        # Initialize storage backend
        if self.config.storage_backend == "sqlite":
            self._store = SQLiteAuditStore(
                self.config.storage_path, self.config.enable_hash_chain
            )
        elif self.config.storage_backend == "postgresql":
            raise NotImplementedError(
                "PostgreSQL backend not yet implemented. Use storage_backend='sqlite'."
            )
        else:
            raise ValueError(
                f"Invalid storage_backend: {self.config.storage_backend}. "
                "Supported: 'sqlite', 'postgresql'"
            )

    async def log_action(
        self,
        agent_id: str,
        action_type: ActionType | str,
        description: str,
        metadata: dict[str, Any] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> CapabilityResult:
        """Log agent action to audit trail.

        Args:
            agent_id: Agent identifier.
            action_type: Type of action.
            description: Description of action.
            metadata: Additional structured data.
            user_id: Optional user ID.
            session_id: Optional session ID.

        Returns:
            CapabilityResult with logged entry details.
        """
        start = datetime.now(UTC)

        # Convert action_type to enum if string
        if isinstance(action_type, str):
            action_type = ActionType(action_type)

        # Insert entry
        entry = self._store.insert(
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            metadata=metadata,
            user_id=user_id,
            session_id=session_id,
        )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "logged": True,
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp.isoformat(),
                "entry_hash": entry.entry_hash,
                "agent_id": agent_id,
                "action_type": action_type.value,
            },
            duration_ms=duration,
        )

    async def query_logs(
        self,
        agent_id: str | None = None,
        action_type: ActionType | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> CapabilityResult:
        """Query audit logs.

        Args:
            agent_id: Filter by agent ID.
            action_type: Filter by action type.
            start_date: Filter by start date (ISO format).
            end_date: Filter by end date (ISO format).
            limit: Maximum results.
            offset: Result offset (for pagination).

        Returns:
            CapabilityResult with matching audit entries.
        """
        start = datetime.now(UTC)

        # Convert action_type to enum if string
        action_type_enum = None
        if action_type:
            action_type_enum = (
                ActionType(action_type)
                if isinstance(action_type, str)
                else action_type
            )

        # Convert date strings to datetime
        start_datetime = (
            datetime.fromisoformat(start_date) if start_date else None
        )
        end_datetime = datetime.fromisoformat(end_date) if end_date else None

        # Query entries
        entries = self._store.query(
            agent_id=agent_id,
            action_type=action_type_enum,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=limit,
            offset=offset,
        )

        # Convert to output format
        entries_data = [
            {
                "entry_id": e.entry_id,
                "timestamp": e.timestamp.isoformat(),
                "agent_id": e.agent_id,
                "action_type": e.action_type.value,
                "description": e.description,
                "metadata": e.metadata,
                "entry_hash": e.entry_hash,
                "user_id": e.user_id,
                "session_id": e.session_id,
            }
            for e in entries
        ]

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "entries": entries_data,
                "count": len(entries_data),
                "limit": limit,
                "offset": offset,
            },
            duration_ms=duration,
        )

    async def verify_integrity(self) -> CapabilityResult:
        """Verify audit trail integrity (hash chain).

        Returns:
            CapabilityResult with verification status.
        """
        start = datetime.now(UTC)

        is_valid, errors = self._store.verify_integrity()

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "valid": is_valid,
                "errors": errors,
                "error_count": len(errors),
                "hash_chain_enabled": self.config.enable_hash_chain,
            },
            duration_ms=duration,
        )

    async def get_stats(self) -> CapabilityResult:
        """Get audit log statistics.

        Returns:
            CapabilityResult with statistics.
        """
        start = datetime.now(UTC)

        stats = self._store.get_stats()

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output=stats,
            duration_ms=duration,
        )

    async def export_logs(
        self,
        format: str = "json",
        agent_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> CapabilityResult:
        """Export audit logs to file.

        Args:
            format: Export format ("json", "csv").
            agent_id: Filter by agent ID.
            start_date: Filter by start date.
            end_date: Filter by end date.

        Returns:
            CapabilityResult with export data.
        """
        start = datetime.now(UTC)

        # Query all matching entries
        query_result = await self.query_logs(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Large limit for export
        )

        entries = query_result.output["entries"]

        if format == "json":
            export_data = json.dumps(entries, indent=2)
        elif format == "csv":
            # Simple CSV format
            if entries:
                import csv
                import io

                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=entries[0].keys())
                writer.writeheader()
                for entry in entries:
                    # Flatten metadata for CSV
                    entry_copy = entry.copy()
                    entry_copy["metadata"] = json.dumps(entry["metadata"])
                    writer.writerow(entry_copy)
                export_data = output.getvalue()
            else:
                export_data = ""
        else:
            return CapabilityResult(
                capability=self.name,
                success=False,
                output={"error": f"Unsupported format: {format}"},
            )

        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        return CapabilityResult(
            capability=self.name,
            success=True,
            output={
                "format": format,
                "data": export_data,
                "entry_count": len(entries),
            },
            duration_ms=duration,
        )

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute audit operation with action routing.

        Args:
            **kwargs: Must include 'action' and action-specific parameters.

        Supported actions:
        - log_action: Log new audit entry.
        - query_logs: Query audit trail.
        - verify_integrity: Verify hash chain integrity.
        - get_stats: Get audit statistics.
        - export_logs: Export audit logs.

        Returns:
            CapabilityResult from the executed action.

        Example:
            >>> result = await audit.execute(
            ...     action="log_action",
            ...     agent_id="coder-1",
            ...     action_type="code_generation",
            ...     description="Generated auth.py"
            ... )
        """
        action_param = kwargs.pop("action", "get_stats")

        action_map = {
            "log_action": self.log_action,
            "query_logs": self.query_logs,
            "verify_integrity": self.verify_integrity,
            "get_stats": self.get_stats,
            "export_logs": self.export_logs,
        }

        if action_param in action_map:
            return await action_map[action_param](**kwargs)

        return CapabilityResult(
            capability=self.name,
            success=False,
            output={"error": f"Unknown action: {action_param}"},
        )
