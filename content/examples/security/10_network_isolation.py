"""Example: Network isolation for secure agent execution.

This example demonstrates:
1. Creating isolated Docker networks
2. Attaching containers to networks
3. Network policy enforcement
4. Inter-container communication
"""

import asyncio

from paracle_isolation import NetworkConfig, NetworkIsolator, NetworkPolicy
from paracle_sandbox import SandboxConfig, SandboxManager


async def main():
    """Run network isolation example."""
    print("=== Network Isolation Example ===\n")

    # Create network isolator
    isolator = NetworkIsolator()

    # Create sandbox manager
    manager = SandboxManager()

    try:
        # 1. Create isolated network
        print("1. Creating isolated network...")
        network_config = NetworkConfig(
            driver="bridge",
            subnet="172.28.0.0/16",
            gateway="172.28.0.1",
            internal=True,  # No external access
            attachable=True,
        )

        network = await isolator.create_network(
            name="paracle-isolated",
            config=network_config,
        )
        print(f"   ✓ Network created: {network.name} ({network.short_id})")

        # 2. Create network policy
        print("\n2. Defining network policy...")
        policy = NetworkPolicy(
            allow_internet=False,  # Block internet
            allow_intra_network=True,  # Allow network-internal
            allowed_ports=[80, 443],  # Only HTTP/HTTPS
            blocked_ips=["10.0.0.0/8"],  # Block private range
        )
        print("   ✓ Policy defined")
        print(f"     - Internet: {policy.allow_internet}")
        print(f"     - Intra-network: {policy.allow_intra_network}")
        print(f"     - Allowed ports: {policy.allowed_ports}")

        # 3. Create sandbox with no network initially
        print("\n3. Creating sandbox...")
        sandbox_config = SandboxConfig(
            base_image="python:3.11-slim",
            network_mode="none",  # Start with no network
        )

        sandbox = await manager.create(sandbox_config)
        print(f"   ✓ Sandbox created: {sandbox.sandbox_id}")

        # 4. Attach sandbox to isolated network
        print("\n4. Attaching sandbox to network...")
        await isolator.attach_container(
            container_id=sandbox.container.id,
            network_id=network.id,
            aliases=["agent-sandbox"],
        )
        print("   ✓ Sandbox attached to network")

        # 5. Get network info
        print("\n5. Network information:")
        info = await isolator.get_network_info(network.id)
        print(f"   Name: {info['name']}")
        print(f"   Driver: {info['driver']}")
        print(f"   Internal: {info['internal']}")
        print(f"   Containers: {len(info['containers'])}")

        # 6. Execute network test
        print("\n6. Testing network connectivity...")
        result = await sandbox.execute(
            ["python3", "-c", "import socket; print('Network test: Can resolve DNS')"]
        )
        print(f"   Exit code: {result['exit_code']}")
        print(f"   Output: {result['stdout'].strip()}")

        # 7. Detach from network
        print("\n7. Detaching from network...")
        await isolator.detach_container(
            container_id=sandbox.container.id,
            network_id=network.id,
        )
        print("   ✓ Sandbox detached")

    finally:
        # Cleanup
        print("\n8. Cleaning up...")
        await manager.destroy_all()
        await isolator.cleanup_all()
        isolator.close()
        print("   ✓ All resources cleaned up")


if __name__ == "__main__":
    asyncio.run(main())
