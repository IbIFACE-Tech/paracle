"""Example: Sandbox execution basics."""

import asyncio

from paracle_sandbox import (
    SandboxConfig,
    SandboxExecutor,
    SandboxManager,
    SandboxMonitor,
)


async def demo_1_simple_execution():
    """Demo 1: Simple agent execution in sandbox."""
    print("\n" + "=" * 60)
    print("Demo 1: Simple Agent Execution")
    print("=" * 60)

    executor = SandboxExecutor()

    agent_code = """
print("Hello from sandbox!")
print("Python version:", __import__('sys').version)
"""

    result = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(cpu_cores=0.5, memory_mb=256),
        monitor=False,
    )

    print(f"\nSuccess: {result['success']}")
    print(f"Output:\n{result['result']['stdout']}")


async def demo_2_with_inputs():
    """Demo 2: Agent execution with inputs."""
    print("\n" + "=" * 60)
    print("Demo 2: Agent with Inputs")
    print("=" * 60)

    executor = SandboxExecutor()

    agent_code = """
import json

# Load inputs
with open('/workspace/inputs.json') as f:
    inputs = json.load(f)

# Process
name = inputs.get('name', 'World')
count = inputs.get('count', 1)

for i in range(count):
    print(f"Hello {name} #{i+1}")
"""

    result = await executor.execute_agent(
        agent_code=agent_code,
        inputs={"name": "Paracle", "count": 3},
        config=SandboxConfig(),
        monitor=False,
    )

    print(f"\nSuccess: {result['success']}")
    print(f"Output:\n{result['result']['stdout']}")


async def demo_3_with_monitoring():
    """Demo 3: Execution with resource monitoring."""
    print("\n" + "=" * 60)
    print("Demo 3: Execution with Monitoring")
    print("=" * 60)

    executor = SandboxExecutor()

    # CPU-intensive code
    agent_code = """
import time

print("Starting CPU-intensive work...")
for i in range(5):
    # Simulate work
    sum(range(1000000))
    print(f"Iteration {i+1} complete")
    time.sleep(0.5)
print("Done!")
"""

    result = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(cpu_cores=1.0, memory_mb=512),
        monitor=True,  # Enable monitoring
    )

    print(f"\nSuccess: {result['success']}")
    print(f"Output:\n{result['result']['stdout']}")

    if "monitoring" in result["stats"]:
        monitoring = result["stats"]["monitoring"]
        print("\nResource Usage:")
        print(f"  Average CPU: {monitoring['averages']['cpu_percent']:.1f}%")
        print(
            f"  Average Memory: {monitoring['averages']['memory_mb']:.1f} MB")
        print(f"  Peak CPU: {monitoring['peaks']['cpu_percent']:.1f}%")
        print(f"  Peak Memory: {monitoring['peaks']['memory_mb']:.1f} MB")


async def demo_4_batch_execution():
    """Demo 4: Batch execution of multiple jobs."""
    print("\n" + "=" * 60)
    print("Demo 4: Batch Execution")
    print("=" * 60)

    executor = SandboxExecutor()

    jobs = [
        {
            "agent_code": f"print('Job {i}: Processing...')\nprint(f'Result: {i * 10}')",
            "inputs": {"job_id": i},
            "monitor": False,
        }
        for i in range(1, 4)
    ]

    results = await executor.execute_batch(jobs, max_concurrent=2)

    print(f"\nCompleted {len(results)} jobs:")
    for i, result in enumerate(results, 1):
        status = "✓" if result["success"] else "✗"
        print(f"\n{status} Job {i}:")
        if result["success"]:
            print(f"  {result['result']['stdout'].strip()}")
        else:
            print(f"  Error: {result.get('error')}")


async def demo_5_error_handling():
    """Demo 5: Error handling and rollback."""
    print("\n" + "=" * 60)
    print("Demo 5: Error Handling")
    print("=" * 60)

    executor = SandboxExecutor()

    # Code that will fail
    agent_code = """
print("Starting...")
x = 1 / 0  # Will cause ZeroDivisionError
print("This won't print")
"""

    result = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(),
        rollback_on_error=True,  # Clean up on error
        monitor=False,
    )

    print(f"\nSuccess: {result['success']}")
    if not result["success"]:
        print(f"Error: {result.get('error')}")
        print(f"Stderr: {result['result']['stderr']}")


async def demo_6_resource_limits():
    """Demo 6: Resource limits enforcement."""
    print("\n" + "=" * 60)
    print("Demo 6: Resource Limits")
    print("=" * 60)

    executor = SandboxExecutor()

    # Memory-intensive code
    agent_code = """
import sys

print("Allocating memory...")
# Try to allocate 1GB (will hit 512MB limit)
data = []
for i in range(100):
    data.append(bytearray(10 * 1024 * 1024))  # 10MB
    print(f"Allocated {(i+1) * 10} MB")
"""

    result = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(
            cpu_cores=0.5,
            memory_mb=512,  # Low memory limit
            timeout_seconds=30,
        ),
        monitor=True,
    )

    print(f"\nSuccess: {result['success']}")
    if not result["success"]:
        print(f"Error: {result.get('error', 'Memory limit exceeded')}")


async def demo_7_network_isolation():
    """Demo 7: Network isolation modes."""
    print("\n" + "=" * 60)
    print("Demo 7: Network Isolation")
    print("=" * 60)

    executor = SandboxExecutor()

    # Test network access
    agent_code = """
import socket

print("Testing network access...")
try:
    socket.create_connection(("google.com", 80), timeout=2)
    print("Network: ACCESSIBLE")
except Exception as e:
    print(f"Network: BLOCKED ({type(e).__name__})")
"""

    # Test with no network
    print("\n1. No network (network_mode='none'):")
    result1 = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(network_mode="none"),
        monitor=False,
    )
    print(result1["result"]["stdout"])

    # Test with bridge network
    print("\n2. Bridge network (network_mode='bridge'):")
    result2 = await executor.execute_agent(
        agent_code=agent_code,
        config=SandboxConfig(network_mode="bridge"),
        monitor=False,
    )
    print(result2["result"]["stdout"])


async def demo_8_manager_context():
    """Demo 8: Using SandboxManager context manager."""
    print("\n" + "=" * 60)
    print("Demo 8: Manager Context")
    print("=" * 60)

    manager = SandboxManager(max_concurrent=2)

    config = SandboxConfig(cpu_cores=0.5, memory_mb=256)

    async with manager.managed_sandbox(config) as sandbox:
        print(f"Created sandbox: {sandbox.sandbox_id[:8]}")

        result = await sandbox.execute("python3 -c 'print(\"Hello from context!\")'")
        print(f"Output: {result['stdout'].strip()}")

    print("Sandbox automatically destroyed")


async def demo_9_monitoring_callbacks():
    """Demo 9: Custom monitoring callbacks."""
    print("\n" + "=" * 60)
    print("Demo 9: Monitoring Callbacks")
    print("=" * 60)

    manager = SandboxManager()
    config = SandboxConfig(cpu_cores=1.0, memory_mb=256)

    sandbox = await manager.create(config)

    def on_warning(stats):
        print("⚠️  WARNING: High resource usage detected!")
        print(
            f"   CPU: {stats['cpu_percent']:.1f}%, Memory: {stats['memory_percent']:.1f}%")

    def on_limit_exceeded(stats):
        print(f"🚨 LIMIT EXCEEDED: {stats}")

    # Create monitor with callbacks
    monitor = SandboxMonitor(
        sandbox,
        interval_seconds=0.5,
        on_warning=on_warning,
        on_limit_exceeded=on_limit_exceeded,
    )

    async with monitor:
        # Run CPU-intensive task
        await sandbox.execute(
            "python3 -c 'import time; [sum(range(10000000)) for _ in range(5)]'"
        )

    print("\nMonitoring complete")
    averages = monitor.get_averages()
    print(f"Average CPU: {averages['cpu_percent']:.1f}%")
    print(f"Average Memory: {averages['memory_mb']:.1f} MB")

    await manager.destroy(sandbox.sandbox_id)


async def main():
    """Run all demos."""
    demos = [
        demo_1_simple_execution,
        demo_2_with_inputs,
        demo_3_with_monitoring,
        demo_4_batch_execution,
        demo_5_error_handling,
        demo_6_resource_limits,
        demo_7_network_isolation,
        demo_8_manager_context,
        demo_9_monitoring_callbacks,
    ]

    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")

    print("\n" + "=" * 60)
    print("All demos complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
