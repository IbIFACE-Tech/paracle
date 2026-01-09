"""Example: Automatic rollback on execution failures.

This example demonstrates:
1. Creating snapshots before execution
2. Automatic rollback on errors
3. Manual rollback to specific snapshot
4. Snapshot management
"""

import asyncio

from paracle_rollback import RollbackConfig, RollbackManager, RollbackPolicy
from paracle_sandbox import SandboxConfig, SandboxManager


async def main():
    """Run rollback example."""
    print("=== Automatic Rollback Example ===\n")

    # Create managers
    sandbox_manager = SandboxManager()
    rollback_config = RollbackConfig(
        policy=RollbackPolicy(
            enabled=True,
            triggers=["on_error", "on_timeout"],
            max_snapshots=3,
        )
    )
    rollback_manager = RollbackManager(config=rollback_config)

    # Create sandbox
    print("1. Creating sandbox...")
    sandbox_config = SandboxConfig(
        base_image="python:3.11-slim",
        network_mode="none",
    )
    sandbox = await sandbox_manager.create(sandbox_config)
    print(f"   ✓ Sandbox created: {sandbox.sandbox_id}\n")

    try:
        # 2. Create initial snapshot
        print("2. Creating initial snapshot...")
        snapshot1_id = await rollback_manager.create_snapshot(
            sandbox.container.id,
            metadata={"stage": "initial", "description": "Clean state"},
        )
        print(f"   ✓ Snapshot created: {snapshot1_id}")

        # 3. Execute successful operation
        print("\n3. Executing successful operation...")
        result = await sandbox.execute(
            [
                "sh",
                "-c",
                "echo 'Creating file' && echo 'test data' > /workspace/test.txt",
            ]
        )
        print(f"   Exit code: {result['exit_code']}")

        # 4. Create snapshot after success
        print("\n4. Creating snapshot after success...")
        snapshot2_id = await rollback_manager.create_snapshot(
            sandbox.container.id,
            metadata={"stage": "after_write", "description": "File created"},
        )
        print(f"   ✓ Snapshot created: {snapshot2_id}")

        # 5. Simulate failure
        print("\n5. Simulating execution failure...")
        try:
            result = await sandbox.execute(
                ["sh", "-c", "rm /workspace/test.txt && exit 1"]  # Delete file and fail
            )
            raise Exception("Simulated failure")
        except Exception as e:
            print(f"   ✗ Execution failed: {e}")

            # 6. Automatic rollback
            print("\n6. Performing automatic rollback...")
            rolled_back = await rollback_manager.auto_rollback_on_error(
                sandbox.container.id, e
            )
            if rolled_back:
                print("   ✓ Automatic rollback successful")
            else:
                print("   ✗ Rollback not triggered")

        # 7. Verify file restored
        print("\n7. Verifying file restoration...")
        result = await sandbox.execute(["sh", "-c", "cat /workspace/test.txt"])
        print(f"   File contents: {result['stdout'].strip()}")
        print("   ✓ File restored successfully!")

        # 8. Manual rollback to initial state
        print("\n8. Manual rollback to initial state...")
        await rollback_manager.rollback(snapshot1_id, sandbox.container.id)
        print("   ✓ Rolled back to initial state")

        # 9. Verify file gone
        print("\n9. Verifying file removed...")
        result = await sandbox.execute(["sh", "-c", "ls /workspace/"])
        print(f"   Workspace contents: {result['stdout'].strip()}")
        print("   ✓ Back to clean state")

        # 10. Snapshot management
        print("\n10. Snapshot information:")
        snapshots = rollback_manager.list_snapshots(sandbox.container.id)
        for snap in snapshots:
            print(
                f"   - {snap['snapshot_id'][:12]}: {snap['metadata'].get('description')}"
            )
            print(f"     Size: {snap['size_mb']:.2f} MB, Created: {snap['timestamp']}")

    finally:
        # Cleanup
        print("\n11. Cleaning up...")

        # Delete snapshots
        for snap_id in list(rollback_manager.snapshots.keys()):
            await rollback_manager.delete_snapshot(snap_id)

        await sandbox_manager.destroy_all()
        rollback_manager.close()
        print("   ✓ All resources cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
