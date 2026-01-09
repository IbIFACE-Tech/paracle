"""Agent factory for creating agents with inheritance and provider integration.

This module provides the AgentFactory class which:
- Resolves agent inheritance chains
- Integrates with the provider registry
- Creates fully configured agent instances
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from paracle_domain.inheritance import InheritanceResult, resolve_inheritance
from paracle_domain.models import Agent, AgentSpec

if TYPE_CHECKING:
    from collections.abc import Callable

    from paracle_providers.base import LLMProvider


class AgentFactoryError(Exception):
    """Base exception for agent factory errors."""

    pass


class ProviderNotAvailableError(AgentFactoryError):
    """Raised when a required provider is not available."""

    def __init__(self, provider_name: str, available_providers: list[str]) -> None:
        self.provider_name = provider_name
        self.available_providers = available_providers
        super().__init__(
            f"Provider '{provider_name}' is not available. "
            f"Available providers: {', '.join(available_providers)}"
        )


class AgentFactory:
    """Factory for creating agents with inheritance resolution and provider integration.

    The factory:
    1. Resolves agent inheritance chains
    2. Validates provider availability
    3. Creates LLM provider instances
    4. Returns fully configured Agent instances

    Example:
        >>> from paracle_providers import ProviderRegistry
        >>> from paracle_store.agent_repository import InMemoryAgentRepository
        >>>
        >>> # Setup
        >>> repository = InMemoryAgentRepository()
        >>> factory = AgentFactory(repository, ProviderRegistry)
        >>>
        >>> # Create agent with inheritance
        >>> spec = AgentSpec(
        ...     name="code-reviewer",
        ...     provider="openai",
        ...     model="gpt-4",
        ...     parent="base-agent"
        ... )
        >>> agent = factory.create(spec)
    """

    def __init__(
        self,
        spec_provider: Callable[[str], AgentSpec | None],
        provider_registry: Any | None = None,
        max_inheritance_depth: int = 5,
        warn_depth: int = 3,
    ) -> None:
        """Initialize the agent factory.

        Args:
            spec_provider: Function to retrieve parent specs by name.
                          Typically: lambda name: repository.get_spec(name)
            provider_registry: Provider registry class (optional).
                              If None, providers won't be instantiated.
            max_inheritance_depth: Maximum allowed inheritance depth
            warn_depth: Depth at which to generate warnings
        """
        self._spec_provider = spec_provider
        self._provider_registry = provider_registry
        self._max_depth = max_inheritance_depth
        self._warn_depth = warn_depth

    def create(
        self,
        spec: AgentSpec,
        provider_config: dict[str, Any] | None = None,
    ) -> Agent:
        """Create an agent from a spec.

        Args:
            spec: Agent specification
            provider_config: Optional configuration for provider initialization

        Returns:
            Agent instance with resolved spec and optional provider

        Raises:
            InheritanceError: If inheritance chain is invalid
            ProviderNotAvailableError: If provider is not available
        """
        # Resolve inheritance
        result = self._resolve_spec(spec)

        # Create agent with resolved spec
        agent = Agent(spec=result.resolved_spec)

        # Attach metadata from resolution
        agent._inheritance_chain = result.chain  # type: ignore
        agent._inheritance_depth = result.depth  # type: ignore
        agent._inheritance_warnings = result.warnings  # type: ignore

        return agent

    def create_with_provider(
        self,
        spec: AgentSpec,
        provider_config: dict[str, Any] | None = None,
    ) -> tuple[Agent, LLMProvider]:
        """Create an agent with its provider instance.

        Args:
            spec: Agent specification
            provider_config: Optional configuration for provider initialization

        Returns:
            Tuple of (Agent, LLMProvider instance)

        Raises:
            InheritanceError: If inheritance chain is invalid
            ProviderNotAvailableError: If provider is not available
            ValueError: If provider registry is not configured
        """
        if self._provider_registry is None:
            raise ValueError(
                "Provider registry not configured. "
                "Pass provider_registry to AgentFactory constructor."
            )

        # Create agent
        agent = self.create(spec, provider_config)

        # Get resolved provider name
        provider_name = agent.spec.provider

        # Check provider availability
        available = self._provider_registry.list_providers()
        if provider_name not in available:
            raise ProviderNotAvailableError(provider_name, available)

        # Create provider instance
        config = provider_config or {}
        provider = self._provider_registry.create_provider(provider_name, **config)

        return agent, provider

    def _resolve_spec(self, spec: AgentSpec) -> InheritanceResult:
        """Resolve agent spec inheritance.

        Args:
            spec: Agent specification to resolve

        Returns:
            InheritanceResult with resolved spec and metadata
        """
        return resolve_inheritance(
            spec=spec,
            get_parent=self._spec_provider,
            max_depth=self._max_depth,
            warn_depth=self._warn_depth,
        )

    def validate_spec(self, spec: AgentSpec) -> list[str]:
        """Validate an agent spec without creating an agent.

        Args:
            spec: Agent specification to validate

        Returns:
            List of validation warnings (empty if valid)

        Raises:
            InheritanceError: If inheritance chain is invalid
        """
        result = self._resolve_spec(spec)
        return result.warnings

    def get_inheritance_chain(self, spec: AgentSpec) -> list[str]:
        """Get the inheritance chain for a spec.

        Args:
            spec: Agent specification

        Returns:
            List of agent names in the inheritance chain (child to root)

        Raises:
            InheritanceError: If inheritance chain is invalid
        """
        result = self._resolve_spec(spec)
        return result.chain

    def preview_resolved_spec(self, spec: AgentSpec) -> AgentSpec:
        """Preview what the resolved spec will look like without creating an agent.

        Args:
            spec: Agent specification

        Returns:
            Resolved agent specification

        Raises:
            InheritanceError: If inheritance chain is invalid
        """
        result = self._resolve_spec(spec)
        return result.resolved_spec
