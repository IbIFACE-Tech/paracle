"""Example: Complete Phase 5 integration.

This example demonstrates the full Phase 5 stack:
1. Sandbox creation with resource limits
2. Network isolation
3. Snapshot before execution
4. Code execution
5. Rollback on failure
6. Artifact review workflow
"""

import asyncio

from paracle_isolation import NetworkConfig, NetworkIsolator
from paracle_review import ReviewConfig, ReviewManager, ReviewPolicy
from paracle_rollback import RollbackConfig, RollbackManager, RollbackPolicy
from paracle_sandbox import SandboxConfig, SandboxManager


async def execute_with_safety(
    sandbox_manager: SandboxManager,
    rollback_manager: RollbackManager,
    review_manager: ReviewManager,
    isolator: NetworkIsolator,
    code: str,
    artifact_desc: str,
):
    """Execute code with full safety mechanisms."""

    # 1. Create isolated network
    print("→ Creating isolated network...")
    network = await isolator.create_network(config=NetworkConfig(internal=True))

    # 2. Create sandbox
    print("→ Creating sandbox...")
    sandbox_config = SandboxConfig(
        base_image="python:3.11-slim",
        cpu_cores=0.5,
        memory_mb=256,
        timeout_seconds=30,
        network_mode="none",
    )
    sandbox = await sandbox_manager.create(sandbox_config)

    # 3. Attach to network
    print("→ Attaching to network...")
    await isolator.attach_container(sandbox.container.id, network.id)

    # 4. Create snapshot
    print("→ Creating snapshot...")
    snapshot_id = await rollback_manager.create_snapshot(
        sandbox.container.id, metadata={"stage": "before_execution"}
    )

    try:
        # 5. Execute code
        print("→ Executing code...")
        result = await sandbox.execute(["python3", "-c", code])

        if result["exit_code"] != 0:
            raise Exception(f"Execution failed: {result['stderr']}")

        print("✓ Execution successful")
        print(f"  Output: {result['stdout'].strip()}")

        # 6. Create review for artifact
        print("→ Creating artifact review...")
        review_id = await review_manager.create_review(
            artifact_id=f"exec-{sandbox.sandbox_id[:8]}",
            artifact_type="command_execution",
            sandbox_id=sandbox.sandbox_id,
            artifact_content={
                "code": code,
                "description": artifact_desc,
                "result": result["stdout"],
            },
        )

        review = await review_manager.get_review(review_id)
        print(f"  Review: {review.status.value} (risk: {review.risk_level})")

        # Auto-approve if needed
        if review.status.value == "pending":
            print("→ Approving review...")
            await review_manager.approve(
                review_id, reviewer="system", comment="Execution successful"
            )

        return result

    except Exception as e:
        print(f"✗ Execution failed: {e}")

        # Automatic rollback
        print("→ Rolling back...")
        rolled_back = await rollback_manager.auto_rollback_on_error(
            sandbox.container.id, e
        )

        if rolled_back:
            print("✓ Rollback successful")

        raise

    finally:
        # Cleanup
        print("→ Cleaning up...")
        await isolator.detach_container(sandbox.container.id, network.id)
        await sandbox_manager.destroy(sandbox.sandbox_id)
        await isolator.remove_network(network.id)


async def main():
    """Run complete Phase 5 integration example."""
    print("=== Complete Phase 5 Integration ===\n")

    # Initialize managers
    sandbox_manager = SandboxManager()

    rollback_manager = RollbackManager(
        config=RollbackConfig(
            policy=RollbackPolicy(
                enabled=True,
                triggers=["on_error"],
            )
        )
    )

    review_manager = ReviewManager(
        config=ReviewConfig(
            policy=ReviewPolicy(
                enabled=True,
                auto_approve_low_risk=True,
            )
        )
    )

    isolator = NetworkIsolator()

    try:
        # Test 1: Successful execution
        print("\n" + "=" * 50)
        print("Test 1: Successful Execution")
        print("=" * 50)

        await execute_with_safety(
            sandbox_manager,
            rollback_manager,
            review_manager,
            isolator,
            code="print('Hello from safe sandbox!')",
            artifact_desc="Simple print statement",
        )

        # Test 2: Failed execution with rollback
        print("\n" + "=" * 50)
        print("Test 2: Failed Execution (with rollback)")
        print("=" * 50)

        try:
            await execute_with_safety(
                sandbox_manager,
                rollback_manager,
                review_manager,
                isolator,
                code="raise Exception('Simulated failure')",
                artifact_desc="Code that fails",
            )
        except Exception:
            print("✓ Failure handled gracefully")

        # Statistics
        print("\n" + "=" * 50)
        print("Final Statistics")
        print("=" * 50)

        print("\nSandbox Manager:")
        stats = await sandbox_manager.get_stats()
        print(f"  Active sandboxes: {stats['total_sandboxes']}")

        print("\nRollback Manager:")
        snapshots = rollback_manager.list_snapshots()
        print(f"  Total snapshots: {len(snapshots)}")

        print("\nReview Manager:")
        reviews = review_manager.list_reviews()
        print(f"  Total reviews: {len(reviews)}")
        print(f"  Approved: {sum(1 for r in reviews if r.status.value == 'approved')}")
        print(f"  Rejected: {sum(1 for r in reviews if r.status.value == 'rejected')}")

    finally:
        print("\n" + "=" * 50)
        print("Cleanup")
        print("=" * 50)

        # Cleanup all
        await sandbox_manager.destroy_all()
        await isolator.cleanup_all()

        # Cleanup snapshots
        for snap_id in list(rollback_manager.snapshots.keys()):
            await rollback_manager.delete_snapshot(snap_id)

        rollback_manager.close()
        isolator.close()

        print("✓ All resources cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
