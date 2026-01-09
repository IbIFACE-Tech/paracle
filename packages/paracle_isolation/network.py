"""Network isolation implementation."""

import logging
from typing import Any

from paracle_core.ids import generate_ulid

import docker
from docker.errors import APIError
from docker.models.networks import Network
from paracle_isolation.config import NetworkConfig, NetworkPolicy
from paracle_isolation.exceptions import NetworkIsolationError

logger = logging.getLogger(__name__)


class NetworkIsolator:
    """Manages Docker networks for sandbox isolation.

    Creates and manages isolated networks with custom policies,
    handles container attachment/detachment, and enforces network rules.

    Attributes:
        networks: Active managed networks
    """

    def __init__(self):
        """Initialize network isolator."""
        self.networks: dict[str, Network] = {}
        self._client: docker.DockerClient | None = None

    def _get_client(self) -> docker.DockerClient:
        """Get or create Docker client.

        Returns:
            Docker client instance
        """
        if not self._client:
            self._client = docker.from_env()
        return self._client

    async def create_network(
        self,
        name: str | None = None,
        config: NetworkConfig | None = None,
        policy: NetworkPolicy | None = None,
    ) -> Network:
        """Create isolated network.

        Args:
            name: Network name (generated if None)
            config: Network configuration
            policy: Network access policy

        Returns:
            Created Docker network

        Raises:
            NetworkIsolationError: If network creation fails
        """
        try:
            client = self._get_client()

            # Generate name if not provided
            if not name:
                name = f"paracle-net-{generate_ulid()}"

            # Use default config if not provided
            if not config:
                config = NetworkConfig()

            # Prepare network options
            ipam_config = None
            if config.subnet or config.gateway:
                ipam_pool = {}
                if config.subnet:
                    ipam_pool["subnet"] = config.subnet
                if config.gateway:
                    ipam_pool["gateway"] = config.gateway

                ipam_config = docker.types.IPAMConfig(
                    pool_configs=[docker.types.IPAMPool(**ipam_pool)]
                )

            # Add policy to labels if provided
            labels = config.labels.copy()
            if policy:
                labels["paracle.policy.internet"] = str(policy.allow_internet)
                labels["paracle.policy.intra_network"] = str(policy.allow_intra_network)

            # Create network
            network = client.networks.create(
                name=name,
                driver=config.driver,
                options=config.options,
                ipam=ipam_config,
                enable_ipv6=config.enable_ipv6,
                internal=config.internal,
                attachable=config.attachable,
                labels=labels,
            )

            # Track network
            self.networks[network.id] = network

            logger.info(
                f"Created network {name} ({network.short_id}): "
                f"driver={config.driver}, internal={config.internal}"
            )

            return network

        except APIError as e:
            raise NetworkIsolationError(f"Failed to create network: {e}") from e

    async def attach_container(
        self,
        container_id: str,
        network_id: str,
        aliases: list[str] | None = None,
    ) -> None:
        """Attach container to network.

        Args:
            container_id: Container ID to attach
            network_id: Network ID to attach to
            aliases: Optional network aliases for container

        Raises:
            NetworkIsolationError: If attachment fails
        """
        try:
            network = self.networks.get(network_id)
            if not network:
                # Try to get network from Docker
                client = self._get_client()
                network = client.networks.get(network_id)

            network.connect(container_id, aliases=aliases)

            logger.info(
                f"Attached container {container_id[:12]} to network {network.name}"
            )

        except APIError as e:
            raise NetworkIsolationError(
                f"Failed to attach container to network: {e}",
                container_id,
            ) from e

    async def detach_container(
        self,
        container_id: str,
        network_id: str,
    ) -> None:
        """Detach container from network.

        Args:
            container_id: Container ID to detach
            network_id: Network ID to detach from

        Raises:
            NetworkIsolationError: If detachment fails
        """
        try:
            network = self.networks.get(network_id)
            if not network:
                client = self._get_client()
                network = client.networks.get(network_id)

            network.disconnect(container_id, force=True)

            logger.info(
                f"Detached container {container_id[:12]} from network {network.name}"
            )

        except APIError as e:
            logger.warning(f"Failed to detach container from network: {e}")

    async def remove_network(self, network_id: str) -> None:
        """Remove network.

        Args:
            network_id: Network ID to remove

        Raises:
            NetworkIsolationError: If removal fails
        """
        try:
            network = self.networks.pop(network_id, None)

            if not network:
                client = self._get_client()
                network = client.networks.get(network_id)

            network.remove()

            logger.info(f"Removed network {network.name} ({network.short_id})")

        except APIError as e:
            logger.warning(f"Failed to remove network: {e}")

    async def get_network_info(self, network_id: str) -> dict[str, Any]:
        """Get network information.

        Args:
            network_id: Network ID

        Returns:
            Dict with network details

        Raises:
            NetworkIsolationError: If network not found
        """
        try:
            network = self.networks.get(network_id)
            if not network:
                client = self._get_client()
                network = client.networks.get(network_id)

            network.reload()

            return {
                "id": network.id,
                "name": network.name,
                "driver": network.attrs.get("Driver"),
                "internal": network.attrs.get("Internal", False),
                "containers": list(network.attrs.get("Containers", {}).keys()),
                "ipam": network.attrs.get("IPAM", {}),
                "labels": network.attrs.get("Labels", {}),
            }

        except APIError as e:
            raise NetworkIsolationError(
                f"Failed to get network info: {e}",
                network_id,
            ) from e

    async def cleanup_all(self) -> None:
        """Remove all managed networks."""
        network_ids = list(self.networks.keys())

        for network_id in network_ids:
            try:
                await self.remove_network(network_id)
            except Exception as e:
                logger.error(f"Failed to remove network {network_id}: {e}")

        logger.info(f"Cleaned up {len(network_ids)} networks")

    def close(self) -> None:
        """Close Docker client."""
        if self._client:
            self._client.close()
            self._client = None
