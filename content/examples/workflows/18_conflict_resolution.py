"""Example: Conflict Resolution for Concurrent Agent Execution.

This example demonstrates how to detect and resolve conflicts
when multiple agents modify the same files concurrently.
"""

import time

from paracle_conflicts import (
    ConflictDetector,
    ConflictResolver,
    LockManager,
    ResolutionStrategy,
)


def main():
    """Run the conflict resolution example."""
    print("=== Paracle Conflict Resolution Example ===\n")

    # 1. Initialize components
    print("1. Initializing conflict management components...")
    lock_manager = LockManager()
    detector = ConflictDetector()
    resolver = ConflictResolver()
    print("   [OK] Components initialized\n")

    # 2. File locking demonstration
    print("2. File locking demonstration...")

    test_file = "example_file.py"

    # Agent 1 acquires lock
    success = lock_manager.acquire_lock(test_file, "agent1", timeout=30)
    print(f"   [OK] Agent1 acquired lock: {success}")

    # Agent 2 tries to acquire same lock
    success = lock_manager.acquire_lock(test_file, "agent2", timeout=30)
    print(f"   [EXPECTED] Agent2 lock denied: {not success}")

    # Check lock status
    lock = lock_manager.get_lock(test_file)
    if lock:
        print(f"   [INFO] File locked by: {lock.agent_id}")
        print(f"   [INFO] Lock expires: {lock.expires_at}\n")

    # Agent 1 releases lock
    lock_manager.release_lock(test_file, "agent1")
    print("   [OK] Agent1 released lock")

    # Now agent 2 can acquire
    success = lock_manager.acquire_lock(test_file, "agent2", timeout=30)
    print(f"   [OK] Agent2 acquired lock: {success}\n")

    lock_manager.release_lock(test_file, "agent2")

    # 3. Conflict detection
    print("3. Conflict detection demonstration...")

    # Simulate two agents modifying the same file
    # (In real usage, this would happen during actual file modifications)
    detector.modifications["config.yaml"] = [
        ("agent1", "abc123"),  # Agent1's version
        ("agent2", "def456"),  # Agent2's version (different hash = conflict)
    ]

    conflicts = detector.get_conflicts(resolved=False)
    print(f"   [INFO] Detected {len(conflicts)} conflict(s)")

    if conflicts:
        for conflict in conflicts:
            print(f"   [CONFLICT] {conflict.file_path}")
            print(f"      Agent1: {conflict.agent1_id}")
            print(f"      Agent2: {conflict.agent2_id}\n")

    # 4. Conflict resolution strategies
    print("4. Testing conflict resolution strategies...\n")

    # Create a mock conflict for demonstration
    from datetime import datetime

    from paracle_conflicts.detector import FileConflict

    mock_conflict = FileConflict(
        file_path="example_config.yaml",
        agent1_id="coder_agent",
        agent2_id="architect_agent",
        agent1_hash="abc123",
        agent2_hash="def456",
        detected_at=datetime.now(datetime.UTC),
    )

    strategies = [
        ResolutionStrategy.FIRST_WINS,
        ResolutionStrategy.LAST_WINS,
        ResolutionStrategy.BACKUP_BOTH,
        ResolutionStrategy.MANUAL,
    ]

    for strategy in strategies:
        result = resolver.resolve(mock_conflict, strategy)
        status = "[OK]" if result.success else "[FAILED]"
        print(f"   {status} {strategy.value}: {result.message}")
        if result.backup_paths:
            for backup in result.backup_paths:
                print(f"        Backup: {backup}")
    print()

    # 5. Wait for lock example
    print("5. Lock waiting demonstration...")

    # Agent 1 acquires lock
    lock_manager.acquire_lock("critical_file.py", "agent1", timeout=5)
    print("   [OK] Agent1 acquired lock on critical_file.py")

    # Agent 2 waits for lock (with timeout)
    print("   [INFO] Agent2 waiting for lock (3 second timeout)...")
    start = time.time()
    success = lock_manager.wait_for_lock(
        "critical_file.py", "agent2", timeout=3, poll_interval=0.5
    )
    elapsed = time.time() - start

    if success:
        print(f"   [OK] Agent2 acquired lock after {elapsed:.1f}s")
    else:
        print(f"   [EXPECTED] Agent2 timeout after {elapsed:.1f}s")

    # Clean up
    lock_manager.release_lock("critical_file.py", "agent1")
    print("   [OK] Agent1 released lock\n")

    # 6. Concurrent execution pattern
    print("6. Recommended concurrent execution pattern:\n")

    pattern = """
    # Safe concurrent file modification:

    def modify_file_safely(file_path, agent_id, modification_fn):
        lock_manager = LockManager()

        # Acquire lock
        if not lock_manager.wait_for_lock(file_path, agent_id, timeout=60):
            raise TimeoutError(f"Could not acquire lock on {file_path}")

        try:
            # Perform modification
            modification_fn(file_path)

            # Record modification for conflict detection
            detector.record_modification(file_path, agent_id)

        finally:
            # Always release lock
            lock_manager.release_lock(file_path, agent_id)
    """

    print(pattern)

    print("\n=== CLI Usage Examples ===\n")
    print("# Show active locks")
    print("paracle conflicts locks\n")

    print("# Acquire lock on file")
    print("paracle conflicts lock src/api.py agent1\n")

    print("# Release lock")
    print("paracle conflicts unlock src/api.py agent1\n")

    print("# Detect conflicts")
    print("paracle conflicts detect\n")

    print("# Resolve conflicts with strategy")
    print("paracle conflicts resolve --strategy last_wins\n")

    print("# List backups")
    print("paracle conflicts backups\n")

    print("# Clean expired locks")
    print("paracle conflicts cleanup\n")

    print("=== Best Practices ===\n")
    print("1. Always acquire locks before modifying shared files")
    print("2. Use appropriate timeouts to prevent deadlocks")
    print("3. Release locks in finally blocks to ensure cleanup")
    print("4. Record modifications for conflict detection")
    print("5. Choose resolution strategy based on use case:")
    print("   - FIRST_WINS: Prioritize stability")
    print("   - LAST_WINS: Prioritize latest changes")
    print("   - BACKUP_BOTH: Preserve all work")
    print("   - MANUAL: Critical files requiring human review")
    print("   - MERGE: Attempt automatic merge (advanced)")


if __name__ == "__main__":
    main()
