"""Remote Agent Registry.

Manages registration and discovery of remote A2A agents.
Remote agents are defined in .parac/agents/manifest.yaml under remote_agents.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from paracle_a2a.config import A2AClientConfig


class RemoteAgentConfig(BaseModel):
    """Configuration for a remote A2A agent."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(
        ...,
        description="Unique agent identifier (used with 'remote:' prefix)",
    )
    name: str = Field(
        ...,
        description="Human-readable agent name",
    )
    url: str = Field(
        ...,
        description="A2A endpoint URL",
    )
    description: str = Field(
        default="",
        description="Agent description",
    )

    # Optional metadata
    provider: str | None = Field(
        default=None,
        description="Provider/organization name",
    )
    version: str | None = Field(
        default=None,
        description="Agent version",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Agent tags for filtering",
    )

    # Connection settings
    auth_type: str | None = Field(
        default=None,
        description="Authentication type: bearer, apiKey",
    )
    auth_token_env: str | None = Field(
        default=None,
        description="Environment variable for auth token",
    )
    timeout_seconds: float = Field(
        default=60.0,
        description="Request timeout in seconds",
    )

    # Capabilities (auto-discovered from Agent Card)
    capabilities: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent capabilities (auto-populated from Agent Card)",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Agent skill IDs (auto-populated from Agent Card)",
    )

    def get_client_config(self) -> A2AClientConfig:
        """Build client config for this agent.

        Returns:
            A2AClientConfig configured for this agent
        """
        import os

        auth_token = None
        if self.auth_token_env:
            auth_token = os.environ.get(self.auth_token_env)

        return A2AClientConfig(
            timeout_seconds=self.timeout_seconds,
            auth_type=self.auth_type,
            auth_token=auth_token,
        )


class RemoteAgentRegistry:
    """Registry for remote A2A agents.

    Loads remote agent definitions from .parac/agents/manifest.yaml
    and provides access to them for the CLI and workflows.
    """

    def __init__(self, parac_root: Path | None = None):
        """Initialize registry.

        Args:
            parac_root: Path to .parac directory
        """
        self.parac_root = parac_root
        self._agents: dict[str, RemoteAgentConfig] = {}
        self._loaded = False

    def _find_parac_root(self) -> Path | None:
        """Find .parac directory."""
        if self.parac_root:
            return self.parac_root

        # Search upward from current directory
        current = Path.cwd()
        while current != current.parent:
            if (current / ".parac").exists():
                return current / ".parac"
            current = current.parent
        return None

    def _load(self) -> None:
        """Load remote agents from manifest."""
        if self._loaded:
            return

        parac_root = self._find_parac_root()
        if not parac_root:
            self._loaded = True
            return

        manifest_path = parac_root / "agents" / "manifest.yaml"
        if not manifest_path.exists():
            self._loaded = True
            return

        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            self._loaded = True
            return

        # Load remote_agents section
        remote_agents = manifest.get("remote_agents", [])
        for agent_data in remote_agents:
            try:
                agent = RemoteAgentConfig(**agent_data)
                self._agents[agent.id] = agent
            except Exception:
                # Skip invalid entries
                pass

        self._loaded = True

    def get(self, agent_id: str) -> RemoteAgentConfig | None:
        """Get remote agent by ID.

        Args:
            agent_id: Agent identifier (without 'remote:' prefix)

        Returns:
            RemoteAgentConfig or None
        """
        self._load()
        return self._agents.get(agent_id)

    def list_all(self) -> list[RemoteAgentConfig]:
        """List all registered remote agents.

        Returns:
            List of RemoteAgentConfig
        """
        self._load()
        return list(self._agents.values())

    def is_remote(self, agent_id: str) -> bool:
        """Check if agent ID refers to a remote agent.

        Args:
            agent_id: Agent identifier (with or without 'remote:' prefix)

        Returns:
            True if agent is remote
        """
        self._load()

        # Check for explicit prefix
        if agent_id.startswith("remote:"):
            return True

        # Check if in registry
        return agent_id in self._agents

    def resolve(self, agent_id: str) -> RemoteAgentConfig | None:
        """Resolve agent ID to remote config.

        Args:
            agent_id: Agent identifier (with or without 'remote:' prefix)

        Returns:
            RemoteAgentConfig or None
        """
        self._load()

        # Strip prefix if present
        clean_id = agent_id.removeprefix("remote:")
        return self._agents.get(clean_id)

    def add(self, agent: RemoteAgentConfig) -> None:
        """Add a remote agent to registry (in-memory only).

        Args:
            agent: Remote agent configuration
        """
        self._load()
        self._agents[agent.id] = agent

    def remove(self, agent_id: str) -> bool:
        """Remove a remote agent from registry (in-memory only).

        Args:
            agent_id: Agent identifier

        Returns:
            True if removed, False if not found
        """
        self._load()
        clean_id = agent_id.removeprefix("remote:")
        if clean_id in self._agents:
            del self._agents[clean_id]
            return True
        return False

    async def discover_and_update(self, agent_id: str) -> RemoteAgentConfig | None:
        """Discover agent capabilities and update registry.

        Fetches the Agent Card from the remote server and updates
        the registry entry with discovered capabilities.

        Args:
            agent_id: Agent identifier

        Returns:
            Updated RemoteAgentConfig or None
        """
        agent = self.resolve(agent_id)
        if not agent:
            return None

        try:
            from paracle_a2a.client import AgentDiscovery

            discovery = AgentDiscovery(agent.get_client_config())
            card = await discovery.discover(agent.url)

            # Update agent with discovered info
            agent.capabilities = {
                "streaming": card.capabilities.streaming,
                "push_notifications": card.capabilities.push_notifications,
            }
            agent.skills = [s.id for s in card.skills]

            return agent

        except Exception:
            return agent


# Global registry instance
_registry: RemoteAgentRegistry | None = None


def get_remote_registry(parac_root: Path | None = None) -> RemoteAgentRegistry:
    """Get or create global remote agent registry.

    Args:
        parac_root: Optional .parac directory path

    Returns:
        RemoteAgentRegistry instance
    """
    global _registry
    if _registry is None or parac_root:
        _registry = RemoteAgentRegistry(parac_root)
    return _registry
