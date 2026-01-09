"""Example: Remote development with SSH transport.

This example demonstrates how to connect to a remote Paracle instance
via SSH and execute commands remotely.

Phase 8.1: Basic SSH Transport
"""

import asyncio

from paracle_transport import RemoteConfig, SSHTransport, TunnelManager
from paracle_transport.remote_config import TunnelConfig


async def example_basic_ssh():
    """Example 1: Basic SSH connection and command execution."""
    print("=== Example 1: Basic SSH Connection ===\n")

    # Configure remote connection
    config = RemoteConfig(
        name="production",
        host="user@prod-server.com",
        workspace="/opt/paracle",
        port=22,
        identity_file="~/.ssh/id_rsa",  # Optional
        tunnels=[
            TunnelConfig(
                local=8000,
                remote=8000,
                description="API server",
            )
        ],
    )

    # Connect and execute commands
    async with SSHTransport(config) as transport:
        print(f"✓ Connected to {config.host}")

        # List agents
        result = await transport.execute("paracle agents list")
        print("\nAvailable agents:")
        print(result["stdout"])

        # Get project status
        result = await transport.execute("paracle status")
        print("\nProject status:")
        print(result["stdout"])


async def example_tunnel_manager():
    """Example 2: Tunnel manager with auto-reconnection."""
    print("\n=== Example 2: Tunnel Manager ===\n")

    config = RemoteConfig(
        name="staging",
        host="user@staging.com",
        workspace="/opt/paracle",
        tunnels=[
            TunnelConfig(local=8000, remote=8000, description="API"),
            TunnelConfig(local=8001, remote=8001, description="MCP WebSocket"),
        ],
    )

    # Use tunnel manager for health monitoring
    async with TunnelManager(config, health_check_interval=10) as manager:
        print(f"✓ Connected with {len(config.tunnels)} tunnels")
        print("✓ Health monitoring enabled")

        # Execute commands via managed transport
        result = await manager.execute("paracle --version")
        print(f"\nRemote Paracle version: {result['stdout'].strip()}")

        # Tunnels are monitored and auto-reconnect if they die
        print("\nTunnels will auto-reconnect on failure...")
        print("Press Ctrl+C to stop\n")

        # Keep running to demonstrate health monitoring
        try:
            await asyncio.sleep(60)  # Run for 1 minute
        except KeyboardInterrupt:
            print("\nStopping...")


async def example_multiple_commands():
    """Example 3: Execute multiple commands in sequence."""
    print("\n=== Example 3: Multiple Commands ===\n")

    config = RemoteConfig(
        name="dev",
        host="user@dev-server.com",
        workspace="/home/user/paracle-project",
    )

    async with SSHTransport(config) as transport:
        commands = [
            "paracle agents list",
            "paracle workflows list",
            "paracle providers list",
            "paracle runs list --limit 5",
        ]

        for cmd in commands:
            print(f"\n$ {cmd}")
            result = await transport.execute(cmd)

            if result["exit_code"] == 0:
                print(result["stdout"])
            else:
                print(f"Error: {result['stderr']}")


def example_config_management():
    """Example 4: Configuration management."""
    print("\n=== Example 4: Configuration Management ===\n")

    # Create remote configs
    production = RemoteConfig(
        name="production",
        host="user@prod.example.com",
        workspace="/opt/paracle",
        port=22,
        tunnels=[TunnelConfig(local=8000, remote=8000)],
    )

    staging = RemoteConfig(
        name="staging",
        host="user@staging.example.com",
        workspace="/opt/paracle",
        port=2222,  # Custom SSH port
        tunnels=[TunnelConfig(local=8001, remote=8000)],
    )

    print("Production config:")
    print(f"  Host: {production.host}")
    print(f"  Username: {production.username}")
    print(f"  Hostname: {production.hostname}")
    print(f"  Workspace: {production.workspace}")
    print(f"  Tunnels: {len(production.tunnels)}")

    print("\nStaging config:")
    print(f"  Host: {staging.host}")
    print(f"  Port: {staging.port}")
    print(f"  Tunnels: {len(staging.tunnels)}")


if __name__ == "__main__":
    import sys

    print("Paracle Remote Development Examples")
    print("=" * 50 + "\n")

    # Check for remote host argument
    if len(sys.argv) > 1 and "@" in sys.argv[1]:
        # Use provided host
        host = sys.argv[1]
        workspace = sys.argv[2] if len(sys.argv) > 2 else "/opt/paracle"

        print(f"Using remote: {host}")
        print(f"Workspace: {workspace}\n")

        config = RemoteConfig(
            name="custom",
            host=host,
            workspace=workspace,
        )

        # Run basic example
        asyncio.run(example_basic_ssh())
    else:
        print("Configuration management (no connection required):")
        example_config_management()

        print("\n" + "=" * 50)
        print("\nTo run remote examples:")
        print("  python 25_remote_development.py user@your-server.com /path/to/workspace")
        print("\nOr use CLI:")
        print("  paracle remote add production user@prod.com /opt/paracle")
        print("  paracle remote test production")
        print("  paracle agents list --remote production")
