"""Example: Using Docker sandbox for isolated agent execution.

This example demonstrates:
1. Creating a sandbox with resource limits
2. Executing code in isolation
3. Monitoring resource usage
4. Automatic cleanup
"""

import asyncio

from paracle_sandbox import SandboxConfig, SandboxManager, SandboxMonitor


async def main():
    """Run sandbox execution example."""
    print("=== Docker Sandbox Example ===\n")

    # Create sandbox manager
    manager = SandboxManager(max_concurrent=5)

    # Configure sandbox with resource limits
    config = SandboxConfig(
        base_image="python:3.11-slim",  # Use Python base image
        cpu_cores=1.0,  # 1 CPU core
        memory_mb=512,  # 512 MB RAM
        disk_mb=1024,  # 1 GB disk
        timeout_seconds=60,  # 60 second timeout
        network_mode="none",  # No network access
        read_only_filesystem=False,  # Allow writes to /workspace
    )

    # Create sandbox
    print("1. Creating sandbox...")
    async with manager.managed_sandbox(config) as sandbox:
        print(f"   ✓ Sandbox created: {sandbox.sandbox_id}\n")

        # Start resource monitor
        print("2. Starting resource monitor...")
        async with SandboxMonitor(sandbox, interval_seconds=0.5) as monitor:
            print("   ✓ Monitor started\n")

            # Execute Python code
            print("3. Executing Python code in sandbox...")
            result = await sandbox.execute(
                [
                    "python3",
                    "-c",
                    "import sys; print(f'Python {sys.version}'); print('Hello from sandbox!')",
                ]
            )

            print(f"   Exit code: {result['exit_code']}")
            print(f"   Output:\n{result['stdout']}")

            # Get resource stats
            print("\n4. Resource usage:")
            stats = await sandbox.get_stats()
            print(f"   CPU: {stats['cpu_percent']:.1f}%")
            print(
                f"   Memory: {stats['memory_mb']:.1f} MB ({stats['memory_percent']:.1f}%)"
            )
            print(f"   Network RX: {stats['network_rx_bytes']} bytes")
            print(f"   Network TX: {stats['network_tx_bytes']} bytes")

            # Get monitor history
            print("\n5. Monitor statistics:")
            averages = monitor.get_averages()
            peaks = monitor.get_peaks()
            print(f"   Avg CPU: {averages['cpu_percent']:.1f}%")
            print(f"   Avg Memory: {averages['memory_mb']:.1f} MB")
            print(f"   Peak CPU: {peaks['cpu_percent']:.1f}%")
            print(f"   Peak Memory: {peaks['memory_mb']:.1f} MB")

    print("\n6. Sandbox cleaned up automatically ✓")

    # Get manager stats
    print("\n7. Manager statistics:")
    stats = await manager.get_stats()
    print(f"   Total sandboxes: {stats['total_sandboxes']}")
    print(f"   Utilization: {stats['utilization']:.0%}")

    # Cleanup
    await manager.destroy_all()
    print("\n✓ All sandboxes destroyed")


if __name__ == "__main__":
    asyncio.run(main())
