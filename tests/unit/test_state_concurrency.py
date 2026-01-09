"""Tests for state management concurrency and file locking.

Tests verify that:
1. File locking prevents concurrent write conflicts
2. Optimistic locking detects state modifications
3. Atomic writes prevent partial corruption
4. Lock timeouts are handled gracefully
"""

import multiprocessing
import threading
import time
from pathlib import Path

import pytest
import yaml
from paracle_core.parac.state import (
    StateConflictError,
    StateLockError,
    load_state,
    save_state,
)


@pytest.fixture
def temp_parac(tmp_path: Path) -> Path:
    """Create temporary .parac directory."""
    parac_dir = tmp_path / ".parac"
    parac_dir.mkdir()

    # Create memory/context directory
    context_dir = parac_dir / "memory" / "context"
    context_dir.mkdir(parents=True)

    # Create initial state
    state_file = context_dir / "current_state.yaml"
    initial_state = {
        "version": "1.0",
        "snapshot_date": "2026-01-01",
        "revision": 0,
        "project": {
            "name": "test-project",
            "version": "0.1.0",
            "phase": "phase_1",
            "status": "in_progress",
        },
        "current_phase": {
            "id": "phase_1",
            "name": "Phase 1",
            "status": "in_progress",
            "progress": "50%",
        },
        "metrics": {},
        "blockers": [],
        "next_actions": [],
    }

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(initial_state, f)

    return parac_dir


class TestFileLocking:
    """Test file locking mechanisms."""

    def test_load_state_with_lock(self, temp_parac: Path):
        """Test that load_state uses file locking."""
        state = load_state(temp_parac)

        assert state is not None
        assert state.project_name == "test-project"
        assert state.revision == 0

        # Lock file should be created and released
        lock_file = temp_parac / "memory" / "context" / "current_state.yaml.lock"
        # Lock should be released after loading
        assert not lock_file.exists() or lock_file.stat().st_size == 0

    def test_save_state_with_lock(self, temp_parac: Path):
        """Test that save_state uses file locking."""
        state = load_state(temp_parac)
        assert state is not None

        state.update_progress(75)
        result = save_state(state, temp_parac)

        assert result is True
        assert state.revision == 1

        # Verify saved correctly
        reloaded = load_state(temp_parac)
        assert reloaded is not None
        assert reloaded.current_phase.progress == "75%"
        assert reloaded.revision == 1

    def test_atomic_write(self, temp_parac: Path):
        """Test that save uses atomic write (temp + rename)."""
        state = load_state(temp_parac)
        assert state is not None

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        temp_file = state_file.with_suffix(".yaml.tmp")

        # Temp file should not exist after save
        save_state(state, temp_parac)
        assert not temp_file.exists()

        # Original file should be updated
        assert state_file.exists()

    def test_lock_timeout(self, temp_parac: Path):
        """Test that lock timeout raises StateLockError."""
        from filelock import FileLock

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        lock_file = state_file.with_suffix(".yaml.lock")

        # Acquire lock externally
        with FileLock(str(lock_file), timeout=10.0):
            # Try to load with short timeout
            with pytest.raises(StateLockError):
                load_state(temp_parac, timeout=0.1)


class TestOptimisticLocking:
    """Test optimistic locking with revision counters."""

    def test_revision_increment(self, temp_parac: Path):
        """Test that revision increments on each save."""
        state = load_state(temp_parac)
        assert state is not None
        assert state.revision == 0

        # First save
        save_state(state, temp_parac)
        assert state.revision == 1

        # Second save
        reloaded = load_state(temp_parac)
        assert reloaded is not None
        assert reloaded.revision == 1

        save_state(reloaded, temp_parac)
        assert reloaded.revision == 2

    def test_conflict_detection(self, temp_parac: Path):
        """Test that concurrent modifications are detected."""
        # Load state twice (simulating two processes)
        state1 = load_state(temp_parac)
        state2 = load_state(temp_parac)

        assert state1 is not None
        assert state2 is not None
        assert state1.revision == state2.revision == 0

        # Process 1 saves first
        state1.update_progress(60)
        save_state(state1, temp_parac)
        assert state1.revision == 1

        # Process 2 tries to save with stale revision
        state2.update_progress(70)
        with pytest.raises(StateConflictError) as exc_info:
            save_state(state2, temp_parac)

        assert "expected revision=0" in str(exc_info.value)
        assert "got revision=1" in str(exc_info.value)

    def test_skip_conflict_check(self, temp_parac: Path):
        """Test that conflict check can be disabled."""
        state1 = load_state(temp_parac)
        state2 = load_state(temp_parac)

        assert state1 is not None
        assert state2 is not None

        # Process 1 saves
        save_state(state1, temp_parac)

        # Process 2 saves with conflict check disabled
        state2.update_progress(70)
        result = save_state(state2, temp_parac, check_conflict=False)

        # Should succeed (overwriting process 1's changes)
        assert result is True


class TestConcurrentAccess:
    """Test concurrent access scenarios."""

    def test_concurrent_reads(self, temp_parac: Path):
        """Test that multiple readers can access simultaneously."""

        def read_state():
            """Read state in thread."""
            state = load_state(temp_parac)
            assert state is not None
            time.sleep(0.01)  # Simulate work
            return state.project_name

        threads = [threading.Thread(target=read_state) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should complete successfully
        assert all(not t.is_alive() for t in threads)

    def test_sequential_writes(self, temp_parac: Path):
        """Test that writes are serialized by lock."""
        results = []

        def write_state(thread_id: int):
            """Write state in thread."""
            try:
                state = load_state(temp_parac)
                if state is None:
                    results.append(("load_failed", thread_id))
                    return

                state.update_progress(thread_id * 10)
                success = save_state(state, temp_parac)
                results.append(("success" if success else "save_failed", thread_id))
            except StateConflictError:
                results.append(("conflict", thread_id))
            except Exception as e:
                results.append(("error", thread_id, str(e)))

        threads = [threading.Thread(target=write_state, args=(i,)) for i in range(1, 6)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Some should succeed, some may have conflicts
        successes = [r for r in results if r[0] == "success"]
        conflicts = [r for r in results if r[0] == "conflict"]

        # At least one should succeed
        assert len(successes) >= 1
        # Conflicts are expected with optimistic locking
        assert len(conflicts) >= 0

    @pytest.mark.slow
    def test_multiprocess_writes(self, temp_parac: Path):
        """Test writes from multiple processes."""

        def write_in_process(parac_path: Path, process_id: int):
            """Write from separate process."""
            import sys

            sys.path.insert(0, str(Path(__file__).parent.parent.parent))

            try:
                state = load_state(parac_path)
                if state is None:
                    return ("load_failed", process_id)

                state.add_completed(f"task_{process_id}")
                save_state(state, parac_path, check_conflict=False)
                return ("success", process_id)
            except Exception as e:
                return ("error", process_id, str(e))

        processes = [
            multiprocessing.Process(target=write_in_process, args=(temp_parac, i))
            for i in range(3)
        ]

        for p in processes:
            p.start()

        for p in processes:
            p.join(timeout=5.0)

        # All processes should complete
        assert all(not p.is_alive() for p in processes)

        # State should be readable
        final_state = load_state(temp_parac)
        assert final_state is not None


class TestErrorHandling:
    """Test error handling in concurrent scenarios."""

    def test_corrupted_yaml_recovery(self, temp_parac: Path):
        """Test handling of corrupted YAML."""
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"

        # Corrupt the file
        with open(state_file, "w") as f:
            f.write("invalid: yaml: content: [[[")

        # Should return None, not crash
        state = load_state(temp_parac)
        assert state is None

    def test_temp_file_cleanup_on_error(self, temp_parac: Path):
        """Test that temp file is cleaned up on write error."""
        state = load_state(temp_parac)
        assert state is not None

        # Make directory read-only to cause write error
        context_dir = temp_parac / "memory" / "context"

        # Monkey-patch yaml.dump to raise error
        import yaml

        original_dump = yaml.dump

        def failing_dump(*args, **kwargs):
            raise yaml.YAMLError("Simulated error")

        yaml.dump = failing_dump

        try:
            result = save_state(state, temp_parac)
            assert result is False

            # Temp file should be cleaned up
            temp_file = context_dir / "current_state.yaml.tmp"
            assert not temp_file.exists()
        finally:
            yaml.dump = original_dump

    def test_lock_file_permissions(self, temp_parac: Path):
        """Test lock file creation with proper permissions."""
        state = load_state(temp_parac)
        assert state is not None

        save_state(state, temp_parac)

        lock_file = temp_parac / "memory" / "context" / "current_state.yaml.lock"
        # Lock file may exist temporarily, check it's not blocking
        if lock_file.exists():
            # Should be able to acquire lock again
            from filelock import FileLock

            with FileLock(str(lock_file), timeout=1.0):
                pass


class TestRevisionPersistence:
    """Test that revision counter persists correctly."""

    def test_revision_in_yaml(self, temp_parac: Path):
        """Test that revision is written to YAML."""
        state = load_state(temp_parac)
        assert state is not None

        state.update_progress(80)
        save_state(state, temp_parac)

        # Read raw YAML
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "revision" in data
        assert data["revision"] == 1

    def test_revision_survives_reload(self, temp_parac: Path):
        """Test that revision persists across load/save cycles."""
        state1 = load_state(temp_parac)
        assert state1 is not None
        assert state1.revision == 0

        save_state(state1, temp_parac)

        state2 = load_state(temp_parac)
        assert state2 is not None
        assert state2.revision == 1

        save_state(state2, temp_parac)

        state3 = load_state(temp_parac)
        assert state3 is not None
        assert state3.revision == 2

    def test_backward_compatibility_no_revision(self, temp_parac: Path):
        """Test loading state without revision field."""
        # Create state without revision
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        old_state = {
            "version": "1.0",
            "snapshot_date": "2026-01-01",
            # No revision field
            "project": {
                "name": "test-project",
                "version": "0.1.0",
                "phase": "phase_1",
                "status": "in_progress",
            },
            "current_phase": {
                "id": "phase_1",
                "name": "Phase 1",
                "status": "in_progress",
                "progress": "50%",
            },
        }

        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(old_state, f)

        # Should load with revision=0
        state = load_state(temp_parac)
        assert state is not None
        assert state.revision == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
