"""Tests for rollback and state management systems."""

import asyncio
import pytest
from datetime import datetime, timezone

from paracle_events import PersistentEventStore, Event, EventType, agent_created
from paracle_orchestration.context import ExecutionContext, ExecutionStatus
from paracle_orchestration.rollback import (
    CheckpointManager,
    CheckpointStatus,
    CompensatingAction,
    CompensationHandler,
    DefaultCompensationHandler,
    RollbackResult,
    StepCheckpoint,
    WorkflowRollbackManager,
    WorkflowTransaction,
)
from paracle_store.snapshot import (
    InMemorySnapshotStore,
    Snapshottable,
    StateSnapshot,
)


# =============================================================================
# Snapshot Tests
# =============================================================================


class TestStateSnapshot:
    """Tests for StateSnapshot model."""

    def test_snapshot_creation(self):
        """Test creating a snapshot."""
        snapshot = StateSnapshot(
            aggregate_id="agent_123",
            aggregate_type="Agent",
            version=1,
            state={"name": "test-agent", "model": "gpt-4"},
        )

        assert snapshot.aggregate_id == "agent_123"
        assert snapshot.aggregate_type == "Agent"
        assert snapshot.version == 1
        assert snapshot.state["name"] == "test-agent"
        assert snapshot.id.startswith("snap_")
        assert snapshot.created_at is not None

    def test_snapshot_immutability(self):
        """Test that snapshots are immutable."""
        snapshot = StateSnapshot(
            aggregate_id="agent_123",
            aggregate_type="Agent",
            version=1,
            state={"name": "test"},
        )

        with pytest.raises(Exception):  # Pydantic ValidationError
            snapshot.version = 2

    def test_snapshot_to_dict(self):
        """Test serialization to dict."""
        snapshot = StateSnapshot(
            aggregate_id="agent_123",
            aggregate_type="Agent",
            version=1,
            state={"name": "test"},
            reason="Initial state",
        )

        data = snapshot.to_dict()
        assert data["aggregate_id"] == "agent_123"
        assert data["version"] == 1
        assert data["reason"] == "Initial state"


class TestInMemorySnapshotStore:
    """Tests for InMemorySnapshotStore."""

    def test_save_and_get(self):
        """Test saving and retrieving snapshots."""
        store = InMemorySnapshotStore()
        snapshot = StateSnapshot(
            aggregate_id="agent_123",
            aggregate_type="Agent",
            version=1,
            state={"name": "test"},
        )

        store.save(snapshot)
        retrieved = store.get(snapshot.id)

        assert retrieved is not None
        assert retrieved.id == snapshot.id
        assert retrieved.aggregate_id == "agent_123"

    def test_get_latest(self):
        """Test getting the latest snapshot for an aggregate."""
        store = InMemorySnapshotStore()

        # Create multiple versions
        for version in range(1, 4):
            snapshot = StateSnapshot(
                aggregate_id="agent_123",
                aggregate_type="Agent",
                version=version,
                state={"version": version},
            )
            store.save(snapshot)

        latest = store.get_latest("agent_123")
        assert latest is not None
        assert latest.version == 3
        assert latest.state["version"] == 3

    def test_get_by_version(self):
        """Test getting a specific version."""
        store = InMemorySnapshotStore()

        for version in range(1, 4):
            snapshot = StateSnapshot(
                aggregate_id="agent_123",
                aggregate_type="Agent",
                version=version,
                state={"version": version},
            )
            store.save(snapshot)

        v2 = store.get_by_version("agent_123", 2)
        assert v2 is not None
        assert v2.version == 2

    def test_get_history(self):
        """Test getting version history."""
        store = InMemorySnapshotStore()

        for version in range(1, 6):
            snapshot = StateSnapshot(
                aggregate_id="agent_123",
                aggregate_type="Agent",
                version=version,
                state={"version": version},
            )
            store.save(snapshot)

        # Get all history
        history = store.get_history("agent_123")
        assert len(history) == 5
        assert history[0].version == 5  # Newest first

        # Get limited history
        history_limited = store.get_history("agent_123", limit=3)
        assert len(history_limited) == 3

    def test_prune(self):
        """Test pruning old snapshots."""
        store = InMemorySnapshotStore()

        for version in range(1, 11):
            snapshot = StateSnapshot(
                aggregate_id="agent_123",
                aggregate_type="Agent",
                version=version,
                state={"version": version},
            )
            store.save(snapshot)

        # Keep only 3 versions
        deleted = store.prune("agent_123", keep_versions=3)
        assert deleted == 7

        history = store.get_history("agent_123")
        assert len(history) == 3
        # Should keep versions 8, 9, 10
        versions = [s.version for s in history]
        assert 10 in versions
        assert 9 in versions
        assert 8 in versions


# =============================================================================
# Persistent Event Store Tests
# =============================================================================


class TestPersistentEventStore:
    """Tests for PersistentEventStore."""

    def test_append_and_get(self):
        """Test appending and retrieving events."""
        store = PersistentEventStore(in_memory=True)

        event = agent_created("agent_123", "test-spec")
        sequence = store.append(event)

        assert sequence == 1

        retrieved = store.get(event.id)
        assert retrieved is not None
        assert retrieved.id == event.id
        assert retrieved.source == "agent_123"

        store.close()

    def test_get_all_in_order(self):
        """Test that events are returned in sequence order."""
        store = PersistentEventStore(in_memory=True)

        events = [
            agent_created("agent_1", "spec1"),
            agent_created("agent_2", "spec2"),
            agent_created("agent_3", "spec3"),
        ]

        for event in events:
            store.append(event)

        all_events = store.get_all()
        assert len(all_events) == 3
        assert all_events[0].source == "agent_1"
        assert all_events[1].source == "agent_2"
        assert all_events[2].source == "agent_3"

        store.close()

    def test_get_by_source(self):
        """Test filtering by source."""
        store = PersistentEventStore(in_memory=True)

        store.append(agent_created("agent_1", "spec1"))
        store.append(agent_created("agent_2", "spec2"))
        store.append(agent_created("agent_1", "spec1"))  # Another for agent_1

        events = store.get_by_source("agent_1")
        assert len(events) == 2

        store.close()

    def test_get_since_sequence(self):
        """Test getting events after a sequence number."""
        store = PersistentEventStore(in_memory=True)

        for i in range(5):
            store.append(agent_created(f"agent_{i}", "spec"))

        events = store.get_since_sequence(2)
        assert len(events) == 3  # Sequences 3, 4, 5

        store.close()

    def test_replay(self):
        """Test replaying events through a handler."""
        store = PersistentEventStore(in_memory=True)

        for i in range(5):
            store.append(agent_created(f"agent_{i}", "spec"))

        replayed = []

        def handler(event):
            replayed.append(event)

        count = store.replay(handler, from_sequence=2)
        assert count == 3
        assert len(replayed) == 3
        assert replayed[0].source == "agent_2"

        store.close()

    def test_checkpoint_save_and_restore(self):
        """Test checkpoint functionality."""
        store = PersistentEventStore(in_memory=True)

        # Append some events
        for i in range(3):
            store.append(agent_created(f"agent_{i}", "spec"))

        # Save checkpoint
        store.save_checkpoint(
            checkpoint_id="chk_1",
            aggregate_id="workflow_123",
            aggregate_type="Workflow",
            state={"step": 3, "completed": ["step1", "step2", "step3"]},
        )

        # Append more events
        for i in range(3, 6):
            store.append(agent_created(f"agent_{i}", "spec"))

        # Restore from checkpoint
        replayed = []
        checkpoint = store.restore_from_checkpoint(
            "chk_1", lambda e: replayed.append(e)
        )

        assert checkpoint is not None
        assert checkpoint["state"]["step"] == 3
        assert len(replayed) == 3  # Events after checkpoint

        store.close()

    def test_export_import_ndjson(self):
        """Test NDJSON export and import."""
        store = PersistentEventStore(in_memory=True)

        for i in range(3):
            store.append(agent_created(f"agent_{i}", "spec"))

        ndjson = store.export_ndjson()
        store.clear()

        assert store.count() == 0

        imported = store.import_ndjson(ndjson)
        assert imported == 3
        assert store.count() == 3

        store.close()


# =============================================================================
# Checkpoint Manager Tests
# =============================================================================


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        manager = CheckpointManager()
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={"query": "test"},
        )
        context.start()

        checkpoint = manager.create_checkpoint(
            execution_id="exec_456",
            step_name="step_1",
            step_index=0,
            step_result={"output": "result"},
            step_inputs={"input": "data"},
            context=context,
            duration_ms=100.0,
        )

        assert checkpoint.execution_id == "exec_456"
        assert checkpoint.step_name == "step_1"
        assert checkpoint.step_index == 0
        assert checkpoint.step_result == {"output": "result"}

    def test_get_checkpoints(self):
        """Test retrieving checkpoints."""
        manager = CheckpointManager()
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        for i in range(5):
            manager.create_checkpoint(
                execution_id="exec_456",
                step_name=f"step_{i}",
                step_index=i,
                step_result={"step": i},
                step_inputs={},
                context=context,
            )

        # Get all checkpoints
        all_checkpoints = manager.get_checkpoints("exec_456")
        assert len(all_checkpoints) == 5

        # Get range
        range_checkpoints = manager.get_checkpoints(
            "exec_456", from_index=1, to_index=3
        )
        assert len(range_checkpoints) == 3

    def test_get_latest_checkpoint(self):
        """Test getting the latest checkpoint."""
        manager = CheckpointManager()
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        for i in range(3):
            manager.create_checkpoint(
                execution_id="exec_456",
                step_name=f"step_{i}",
                step_index=i,
                step_result={"step": i},
                step_inputs={},
                context=context,
            )

        latest = manager.get_latest_checkpoint("exec_456")
        assert latest is not None
        assert latest.step_index == 2
        assert latest.step_name == "step_2"


# =============================================================================
# Workflow Rollback Tests
# =============================================================================


class MockCompensationHandler(CompensationHandler):
    """Mock handler for testing compensation."""

    def __init__(self):
        self.compensated_steps = []
        self.fail_steps = set()

    async def compensate(
        self,
        action: CompensatingAction,
        checkpoint: StepCheckpoint,
    ) -> bool:
        if action.step_name in self.fail_steps:
            return False
        self.compensated_steps.append(action.step_name)
        return True

    def can_handle(self, action: CompensatingAction) -> bool:
        return action.action_type == "mock"


class TestWorkflowRollbackManager:
    """Tests for WorkflowRollbackManager."""

    @pytest.mark.asyncio
    async def test_rollback_all_steps(self):
        """Test rolling back all steps."""
        manager = WorkflowRollbackManager()
        mock_handler = MockCompensationHandler()
        manager.add_handler(mock_handler)

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        # Create checkpoints and register compensations
        for i in range(3):
            step_name = f"step_{i}"
            manager.create_checkpoint(
                execution_id="exec_456",
                step_name=step_name,
                step_index=i,
                step_result={"step": i},
                step_inputs={},
                context=context,
            )
            manager.register_compensation(
                step_name,
                CompensatingAction(step_name=step_name, action_type="mock"),
            )

        # Rollback all
        result = await manager.rollback("exec_456")

        assert result.success
        assert len(result.steps_compensated) == 3
        assert "step_2" in result.steps_compensated
        assert "step_1" in result.steps_compensated
        assert "step_0" in result.steps_compensated

    @pytest.mark.asyncio
    async def test_rollback_to_specific_step(self):
        """Test rolling back to a specific step."""
        manager = WorkflowRollbackManager()
        mock_handler = MockCompensationHandler()
        manager.add_handler(mock_handler)

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        for i in range(5):
            step_name = f"step_{i}"
            manager.create_checkpoint(
                execution_id="exec_456",
                step_name=step_name,
                step_index=i,
                step_result={"step": i},
                step_inputs={},
                context=context,
            )
            manager.register_compensation(
                step_name,
                CompensatingAction(step_name=step_name, action_type="mock"),
            )

        # Rollback to step 2 (should compensate steps 3, 4)
        result = await manager.rollback("exec_456", to_step_index=2)

        assert result.success
        assert len(result.steps_compensated) == 2
        assert "step_4" in result.steps_compensated
        assert "step_3" in result.steps_compensated
        assert "step_2" not in result.steps_compensated

    @pytest.mark.asyncio
    async def test_rollback_with_failure(self):
        """Test rollback when compensation fails."""
        manager = WorkflowRollbackManager()
        mock_handler = MockCompensationHandler()
        mock_handler.fail_steps.add("step_1")  # This step will fail
        manager.add_handler(mock_handler)

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        for i in range(3):
            step_name = f"step_{i}"
            manager.create_checkpoint(
                execution_id="exec_456",
                step_name=step_name,
                step_index=i,
                step_result={"step": i},
                step_inputs={},
                context=context,
            )
            manager.register_compensation(
                step_name,
                CompensatingAction(
                    step_name=step_name, action_type="mock", required=True
                ),
            )

        result = await manager.rollback("exec_456")

        assert not result.success  # Failed due to required compensation failure
        assert "step_2" in result.steps_compensated  # This one succeeded
        assert len(result.errors) > 0

    def test_get_rollback_plan(self):
        """Test getting rollback plan without executing."""
        manager = WorkflowRollbackManager()

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        for i in range(3):
            step_name = f"step_{i}"
            manager.create_checkpoint(
                execution_id="exec_456",
                step_name=step_name,
                step_index=i,
                step_result={"step": i},
                step_inputs={},
                context=context,
            )
            manager.register_compensation(
                step_name,
                CompensatingAction(step_name=step_name, action_type="cleanup"),
            )

        plan = manager.get_rollback_plan("exec_456", to_step_index=0)

        assert len(plan) == 2  # Steps 1 and 2 should be rolled back
        assert plan[0][0].step_name == "step_2"  # Reverse order
        assert plan[1][0].step_name == "step_1"


# =============================================================================
# Workflow Transaction Tests
# =============================================================================


class TestWorkflowTransaction:
    """Tests for WorkflowTransaction."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """Test successful transaction commit."""
        manager = WorkflowRollbackManager()
        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        async with WorkflowTransaction(manager, "exec_456") as tx:
            tx.checkpoint("step_1", {"result": 1}, context)
            tx.checkpoint("step_2", {"result": 2}, context)

        assert tx.is_committed
        assert not tx.is_rolled_back

    @pytest.mark.asyncio
    async def test_transaction_auto_rollback(self):
        """Test automatic rollback on exception."""
        manager = WorkflowRollbackManager()
        mock_handler = MockCompensationHandler()
        manager.add_handler(mock_handler)

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        with pytest.raises(ValueError):
            async with WorkflowTransaction(manager, "exec_456") as tx:
                tx.checkpoint("step_1", {"result": 1}, context)
                manager.register_compensation(
                    "step_1",
                    CompensatingAction(step_name="step_1", action_type="mock"),
                )

                tx.checkpoint("step_2", {"result": 2}, context)
                manager.register_compensation(
                    "step_2",
                    CompensatingAction(step_name="step_2", action_type="mock"),
                )

                # Simulate failure
                raise ValueError("Step 3 failed!")

        assert tx.is_rolled_back
        assert not tx.is_committed
        # Both steps should have been compensated
        assert "step_1" in mock_handler.compensated_steps
        assert "step_2" in mock_handler.compensated_steps

    @pytest.mark.asyncio
    async def test_transaction_manual_rollback(self):
        """Test manual rollback within transaction."""
        manager = WorkflowRollbackManager()
        mock_handler = MockCompensationHandler()
        manager.add_handler(mock_handler)

        context = ExecutionContext(
            workflow_id="wf_123",
            execution_id="exec_456",
            inputs={},
        )
        context.start()

        async with WorkflowTransaction(manager, "exec_456", auto_rollback=False) as tx:
            tx.checkpoint("step_1", {"result": 1}, context)
            manager.register_compensation(
                "step_1",
                CompensatingAction(step_name="step_1", action_type="mock"),
            )

            # Decide to rollback manually
            result = await tx.rollback()

            assert result.success
            assert tx.is_rolled_back
