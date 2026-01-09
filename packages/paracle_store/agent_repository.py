"""Agent repository implementation.

Specialized repository for Agent entities with additional query methods.
"""

from __future__ import annotations

from paracle_domain.models import Agent, AgentSpec, EntityStatus

from paracle_store.repository import InMemoryRepository


class AgentRepository(InMemoryRepository[Agent]):
    """Repository for Agent entities."""

    def __init__(self) -> None:
        """Initialize agent repository."""
        super().__init__(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )
        self._specs: dict[str, AgentSpec] = {}

    def register_spec(self, spec: AgentSpec) -> AgentSpec:
        """Register an agent spec.

        Specs are templates for creating agents.
        Multiple agents can be created from the same spec.

        Args:
            spec: Agent specification to register

        Returns:
            Registered spec
        """
        self._specs[spec.name] = spec
        return spec

    def get_spec(self, name: str) -> AgentSpec | None:
        """Get an agent spec by name.

        Args:
            name: Spec name

        Returns:
            AgentSpec if found, None otherwise
        """
        return self._specs.get(name)

    def list_specs(self) -> list[AgentSpec]:
        """List all registered specs.

        Returns:
            List of all agent specs
        """
        return list(self._specs.values())

    def remove_spec(self, name: str) -> bool:
        """Remove an agent spec.

        Args:
            name: Spec name to remove

        Returns:
            True if removed, False if not found
        """
        if name not in self._specs:
            return False
        del self._specs[name]
        return True

    def create_from_spec(
        self,
        spec_name: str,
        resolved_spec: AgentSpec | None = None,
    ) -> Agent:
        """Create an agent from a registered spec.

        Args:
            spec_name: Name of the spec to use
            resolved_spec: Optional resolved spec (after inheritance)

        Returns:
            Created agent

        Raises:
            ValueError: If spec not found
        """
        spec = self.get_spec(spec_name)
        if spec is None:
            raise ValueError(f"Spec '{spec_name}' not found")

        agent = Agent(spec=spec, resolved_spec=resolved_spec)
        return self.add(agent)

    def find_by_status(self, status: EntityStatus) -> list[Agent]:
        """Find agents by status.

        Args:
            status: Status to filter by

        Returns:
            List of matching agents
        """
        return self.find_by(lambda a: a.status.phase == status)

    def find_by_spec_name(self, spec_name: str) -> list[Agent]:
        """Find agents by spec name.

        Args:
            spec_name: Spec name to filter by

        Returns:
            List of matching agents
        """
        return self.find_by(lambda a: a.spec.name == spec_name)

    def find_active(self) -> list[Agent]:
        """Find all active/running agents.

        Returns:
            List of active agents
        """
        return self.find_by(
            lambda a: a.status.phase in (EntityStatus.ACTIVE, EntityStatus.RUNNING)
        )

    def find_by_provider(self, provider: str) -> list[Agent]:
        """Find agents by provider.

        Args:
            provider: Provider to filter by (e.g., "openai", "anthropic")

        Returns:
            List of matching agents
        """
        return self.find_by(lambda a: a.get_effective_spec().provider == provider)
