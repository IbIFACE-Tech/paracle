"""Paracle Isolation - Network and resource isolation for sandboxes.

This package provides network isolation, custom networks, and
inter-container communication controls for secure sandbox execution.

Components:
- NetworkIsolator: Manages Docker networks for isolation
- NetworkPolicy: Defines network access rules
- NetworkConfig: Network configuration settings

Example:
    ```python
    from paracle_isolation import NetworkIsolator, NetworkPolicy

    # Create network isolator
    isolator = NetworkIsolator()

    # Create isolated network
    network = await isolator.create_network("agent-network")

    # Attach sandbox to network
    await isolator.attach_container(container_id, network.id)
    ```
"""

from paracle_isolation.config import NetworkConfig, NetworkPolicy
from paracle_isolation.exceptions import IsolationError, NetworkIsolationError
from paracle_isolation.network import NetworkIsolator

__all__ = [
    "NetworkIsolator",
    "NetworkConfig",
    "NetworkPolicy",
    "IsolationError",
    "NetworkIsolationError",
]
