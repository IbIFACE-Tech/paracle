"""Unit tests for AuditCapability."""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from paracle_core.compat import UTC
from paracle_meta.capabilities.audit import (
    ActionType,
    AuditCapability,
    AuditConfig,
    AuditEntry,
    SQLiteAuditStore,
)


@pytest.fixture
def audit_store(tmp_path):
    """Create temporary SQLite audit store."""
    db_path = tmp_path / "test_audit.db"
    store = SQLiteAuditStore(str(db_path))
    return store


@pytest.fixture
def audit(tmp_path):
    """Create AuditCapability instance with temporary storage."""
    db_path = tmp_path / "test_audit.db"
    config = AuditConfig(
        storage_backend="sqlite",
        storage_path=str(db_path),
        enable_hash_chain=True,
        retention_days=30,
    )
    return AuditCapability(config)


# ==============================================================================
# AuditEntry Unit Tests
# ==============================================================================


def test_audit_entry_initialization():
    """Test AuditEntry initialization."""
    now = datetime.now(UTC)
    entry = AuditEntry(
        entry_id=1,
        timestamp=now,
        agent_id="test-agent",
        action_type=ActionType.CODE_GENERATION,
        description="Test action",
        metadata={"key": "value"},
        previous_hash="previous-hash",
        entry_hash="entry-hash",
    )

    assert entry.entry_id == 1
    assert entry.agent_id == "test-agent"
    assert entry.action_type == ActionType.CODE_GENERATION
    assert entry.metadata == {"key": "value"}


def test_audit_entry_defaults():
    """Test AuditEntry default values."""
    now = datetime.now(UTC)
    entry = AuditEntry(
        entry_id=1,
        timestamp=now,
        agent_id="test-agent",
        action_type=ActionType.FILE_READ,
        description="Test",
    )

    assert entry.metadata == {}
    assert entry.previous_hash == ""
    assert entry.entry_hash == ""


# ==============================================================================
# SQLiteAuditStore Unit Tests
# ==============================================================================


def test_sqlite_store_insert_first_entry(audit_store):
    """Test inserting first entry (no previous hash)."""
    entry = audit_store.insert(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Generate code",
        metadata={"language": "python"},
    )

    assert entry.entry_id is not None
    assert entry.agent_id == "agent-1"
    assert entry.action_type == ActionType.CODE_GENERATION
    assert entry.description == "Generate code"
    assert entry.metadata == {"language": "python"}
    assert entry.previous_hash == ""  # First entry
    assert entry.entry_hash is not None  # Hash calculated
    assert len(entry.entry_hash) == 64  # SHA-256 hex length


def test_sqlite_store_insert_chain(audit_store):
    """Test hash chain creation."""
    # Insert first entry
    entry1 = audit_store.insert(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Action 1",
    )

    # Insert second entry
    entry2 = audit_store.insert(
        agent_id="agent-1",
        action_type=ActionType.CODE_EXECUTION,
        description="Action 2",
    )

    # Verify chain links
    assert entry1.previous_hash == ""
    assert entry2.previous_hash == entry1.entry_hash
    assert entry2.entry_hash != entry1.entry_hash


def test_sqlite_store_query_all(audit_store):
    """Test querying all entries."""
    # Insert multiple entries
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 1"
    )
    audit_store.insert(
        agent_id="agent-2", action_type=ActionType.FILE_WRITE, description="Write 1"
    )
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 2"
    )

    # Query all
    entries = audit_store.query()

    assert len(entries) == 3
    assert all(isinstance(e, AuditEntry) for e in entries)


def test_sqlite_store_query_by_agent(audit_store):
    """Test querying by agent ID."""
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 1"
    )
    audit_store.insert(
        agent_id="agent-2", action_type=ActionType.FILE_WRITE, description="Write 1"
    )
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 2"
    )

    entries = audit_store.query(agent_id="agent-1")

    assert len(entries) == 2
    assert all(e.agent_id == "agent-1" for e in entries)


def test_sqlite_store_query_by_action_type(audit_store):
    """Test querying by action type."""
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 1"
    )
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_WRITE, description="Write 1"
    )
    audit_store.insert(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 2"
    )

    entries = audit_store.query(action_type=ActionType.FILE_READ)

    assert len(entries) == 2
    assert all(e.action_type == ActionType.FILE_READ for e in entries)


def test_sqlite_store_query_limit(audit_store):
    """Test query limit."""
    for i in range(10):
        audit_store.insert(
            agent_id="agent-1",
            action_type=ActionType.FILE_READ,
            description=f"Action {i}",
        )

    entries = audit_store.query(limit=5)
    assert len(entries) == 5


def test_sqlite_store_verify_integrity_valid(audit_store):
    """Test integrity verification for valid chain."""
    # Insert multiple entries
    for i in range(5):
        audit_store.insert(
            agent_id="agent-1",
            action_type=ActionType.CODE_GENERATION,
            description=f"Action {i}",
        )

    is_valid, errors = audit_store.verify_integrity()

    assert is_valid is True
    assert len(errors) == 0


def test_sqlite_store_get_stats(audit_store):
    """Test getting statistics."""
    # Insert entries with different types and agents
    audit_store.insert(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Gen 1",
    )
    audit_store.insert(
        agent_id="agent-1",
        action_type=ActionType.CODE_EXECUTION,
        description="Exec 1",
    )
    audit_store.insert(
        agent_id="agent-2", action_type=ActionType.FILE_WRITE, description="Write 1"
    )

    stats = audit_store.get_stats()

    assert stats["total_entries"] == 3
    assert len(stats["by_agent"]) == 2
    assert ActionType.CODE_GENERATION.value in stats["by_action_type"]
    assert stats["by_action_type"][ActionType.CODE_GENERATION.value] == 1


# ==============================================================================
# AuditCapability Initialization Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_audit_initialization(audit):
    """Test AuditCapability initialization."""
    assert audit.name == "audit"
    assert audit.config.storage_backend == "sqlite"
    assert audit.config.enable_hash_chain is True


@pytest.mark.asyncio
async def test_invalid_storage_backend():
    """Test that invalid storage backend raises error."""
    config = AuditConfig(storage_backend="invalid")

    with pytest.raises(ValueError, match="Invalid storage_backend"):
        AuditCapability(config)


# ==============================================================================
# log_action Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_log_action_basic(audit):
    """Test logging basic action."""
    result = await audit.log_action(
        agent_id="test-agent",
        action_type=ActionType.CODE_GENERATION,
        description="Generated user authentication module",
        metadata={"language": "python", "lines": 150},
    )

    assert result.success is True
    assert result.output["logged"] is True
    assert "entry_id" in result.output
    assert "entry_hash" in result.output
    assert len(result.output["entry_hash"]) == 64


@pytest.mark.asyncio
async def test_log_action_with_metadata(audit):
    """Test logging action with metadata."""
    result = await audit.log_action(
        agent_id="test-agent",
        action_type=ActionType.FILE_WRITE,
        description="Modified production config",
        metadata={"file": "config.yaml", "changes": 5},
    )

    assert result.success is True
    assert "entry_id" in result.output
    assert "entry_hash" in result.output


@pytest.mark.asyncio
async def test_log_action_creates_chain(audit):
    """Test that logging creates hash chain."""
    result1 = await audit.log_action(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Action 1",
    )

    result2 = await audit.log_action(
        agent_id="agent-1",
        action_type=ActionType.CODE_EXECUTION,
        description="Action 2",
    )

    # Both should succeed
    assert result1.success is True
    assert result2.success is True
    # Hashes should be different
    assert result1.output["entry_hash"] != result2.output["entry_hash"]


@pytest.mark.asyncio
async def test_log_action_enum_conversion(audit):
    """Test that action_type string is converted to enum."""
    result = await audit.log_action(
        agent_id="test-agent",
        action_type="code_generation",  # String instead of enum
        description="Test",
    )

    assert result.success is True


# ==============================================================================
# query_logs Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_query_logs_all(audit):
    """Test querying all logs."""
    # Insert test data
    await audit.log_action(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 1"
    )
    await audit.log_action(
        agent_id="agent-2", action_type=ActionType.FILE_WRITE, description="Write 1"
    )

    result = await audit.query_logs()

    assert result.success is True
    assert result.output["count"] == 2
    assert len(result.output["entries"]) == 2


@pytest.mark.asyncio
async def test_query_logs_by_agent(audit):
    """Test querying logs by agent."""
    await audit.log_action(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 1"
    )
    await audit.log_action(
        agent_id="agent-2", action_type=ActionType.FILE_WRITE, description="Write 1"
    )
    await audit.log_action(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 2"
    )

    result = await audit.query_logs(agent_id="agent-1")

    assert result.success is True
    assert result.output["count"] == 2
    assert all(e["agent_id"] == "agent-1" for e in result.output["entries"])


@pytest.mark.asyncio
async def test_query_logs_by_action_type(audit):
    """Test querying logs by action type."""
    await audit.log_action(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 1"
    )
    await audit.log_action(
        agent_id="agent-1", action_type=ActionType.FILE_WRITE, description="Write 1"
    )
    await audit.log_action(
        agent_id="agent-1", action_type=ActionType.FILE_READ, description="Read 2"
    )

    result = await audit.query_logs(action_type=ActionType.FILE_READ)

    assert result.success is True
    assert result.output["count"] == 2
    assert all(
        e["action_type"] == ActionType.FILE_READ.value
        for e in result.output["entries"]
    )


@pytest.mark.asyncio
async def test_query_logs_limit(audit):
    """Test query limit."""
    for i in range(10):
        await audit.log_action(
            agent_id="agent-1",
            action_type=ActionType.FILE_READ,
            description=f"Action {i}",
        )

    result = await audit.query_logs(limit=5)

    assert result.success is True
    assert len(result.output["entries"]) == 5


# ==============================================================================
# verify_integrity Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_verify_integrity_valid(audit):
    """Test integrity verification for valid chain."""
    # Insert multiple entries
    for i in range(5):
        await audit.log_action(
            agent_id="agent-1",
            action_type=ActionType.CODE_GENERATION,
            description=f"Action {i}",
        )

    result = await audit.verify_integrity()

    assert result.success is True
    assert result.output["valid"] is True
    assert result.output["error_count"] == 0
    assert len(result.output["errors"]) == 0


# ==============================================================================
# get_stats Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_get_stats(audit):
    """Test getting statistics."""
    # Insert test data
    await audit.log_action(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Gen 1",
    )
    await audit.log_action(
        agent_id="agent-1",
        action_type=ActionType.CODE_EXECUTION,
        description="Exec 1",
    )
    await audit.log_action(
        agent_id="agent-2", action_type=ActionType.FILE_WRITE, description="Write 1"
    )

    result = await audit.get_stats()

    assert result.success is True
    assert result.output["total_entries"] == 3
    assert len(result.output["by_agent"]) == 2
    assert ActionType.CODE_GENERATION.value in result.output["by_action_type"]
    assert "earliest_entry" in result.output
    assert "latest_entry" in result.output


# ==============================================================================
# export_logs Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_export_logs_json(audit):
    """Test exporting logs to JSON."""
    # Insert test data
    await audit.log_action(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Test action",
    )

    result = await audit.export_logs(format="json")

    assert result.success is True
    assert result.output["format"] == "json"
    assert result.output["entry_count"] == 1
    assert "data" in result.output

    # Verify JSON content
    data = json.loads(result.output["data"])
    assert len(data) == 1
    assert data[0]["agent_id"] == "agent-1"
    assert data[0]["description"] == "Test action"


@pytest.mark.asyncio
async def test_export_logs_csv(audit):
    """Test exporting logs to CSV."""
    await audit.log_action(
        agent_id="agent-1",
        action_type=ActionType.CODE_GENERATION,
        description="Test action",
    )

    result = await audit.export_logs(format="csv")

    assert result.success is True
    assert result.output["format"] == "csv"
    assert result.output["entry_count"] == 1

    # Verify CSV content
    csv_data = result.output["data"]
    assert "entry_id" in csv_data
    assert "agent_id" in csv_data
    assert "agent-1" in csv_data


@pytest.mark.asyncio
async def test_export_logs_invalid_format(audit):
    """Test that invalid format raises error."""
    result = await audit.export_logs(format="invalid")

    assert result.success is False
    assert "error" in result.output


# ==============================================================================
# execute Action Routing Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_execute_log_action(audit):
    """Test execute with log_action action."""
    result = await audit.execute(
        action="log_action",
        agent_id="test-agent",
        action_type=ActionType.CODE_GENERATION,
        description="Test",
    )

    assert result.success is True
    assert result.output["logged"] is True


@pytest.mark.asyncio
async def test_execute_default_action(audit):
    """Test execute with default action (get_stats)."""
    await audit.log_action(
        agent_id="test-agent", action_type=ActionType.FILE_READ, description="Test"
    )

    result = await audit.execute()  # Default action is get_stats

    assert result.success is True
    assert result.output["total_entries"] >= 1


@pytest.mark.asyncio
async def test_execute_unknown_action(audit):
    """Test execute with unknown action."""
    result = await audit.execute(action="invalid_action")

    assert result.success is False
    assert "error" in result.output
    assert "Unknown action" in result.output["error"]


# ==============================================================================
# Integration Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_full_audit_workflow(audit):
    """Test complete audit workflow."""
    # 1. Log multiple actions
    await audit.log_action(
        agent_id="coder",
        action_type=ActionType.CODE_GENERATION,
        description="Generated authentication module",
        metadata={"language": "python", "lines": 150},
    )

    await audit.log_action(
        agent_id="coder",
        action_type=ActionType.CODE_EXECUTION,
        description="Ran unit tests",
        metadata={"test_count": 42, "passed": 42},
    )

    await audit.log_action(
        agent_id="reviewer",
        action_type=ActionType.FILE_READ,
        description="Reviewed authentication.py",
        metadata={"file": "auth.py"},
    )

    # 2. Query logs
    all_logs = await audit.query_logs()
    assert all_logs.output["count"] == 3

    coder_logs = await audit.query_logs(agent_id="coder")
    assert coder_logs.output["count"] == 2

    # 3. Verify integrity
    integrity = await audit.verify_integrity()
    assert integrity.output["valid"] is True

    # 4. Get statistics
    stats = await audit.get_stats()
    assert stats.output["total_entries"] == 3
    assert len(stats.output["by_agent"]) == 2

    # 5. Export logs
    export_result = await audit.export_logs(format="json")
    assert export_result.success is True
    assert export_result.output["entry_count"] == 3


@pytest.mark.asyncio
async def test_concurrent_logging(audit):
    """Test concurrent log operations."""

    async def log_action_wrapper(agent_id: str, action_num: int):
        return await audit.log_action(
            agent_id=agent_id,
            action_type=ActionType.CODE_GENERATION,
            description=f"Action {action_num}",
        )

    # Log 10 actions concurrently
    results = await asyncio.gather(
        *[log_action_wrapper("agent-1", i) for i in range(10)]
    )

    assert all(r.success for r in results)

    # Verify all logged
    query_result = await audit.query_logs()
    assert query_result.output["count"] == 10

    # Verify integrity maintained
    integrity = await audit.verify_integrity()
    assert integrity.output["valid"] is True
