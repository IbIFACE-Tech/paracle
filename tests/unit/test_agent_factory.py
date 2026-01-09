"""Tests for Agent Factory."""

import pytest

from paracle_domain import (
    AgentFactory,
    AgentFactoryError,
    AgentSpec,
    CircularInheritanceError,
    MaxDepthExceededError,
    ParentNotFoundError,
    ProviderNotAvailableError,
)


class MockProviderRegistry:
    """Mock provider registry for testing."""

    _providers = {"openai": "MockOpenAI", "anthropic": "MockAnthropic"}

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def create_provider(cls, name: str, **config):
        if name not in cls._providers:
            raise ValueError(f"Provider {name} not found")
        return f"Provider:{name}"


class TestAgentFactory:
    """Tests for AgentFactory."""

    def test_create_simple_agent(self):
        """Test creating an agent without inheritance."""
        spec = AgentSpec(name="test-agent", provider="openai", model="gpt-4")

        def get_parent(name: str):
            return None

        factory = AgentFactory(get_parent)
        agent = factory.create(spec)

        assert agent.spec.name == "test-agent"
        assert agent.spec.model == "gpt-4"
        assert agent.spec.provider == "openai"

    def test_create_agent_with_inheritance(self):
        """Test creating an agent with parent inheritance."""
        base = AgentSpec(
            name="base-agent",
            provider="openai",
            model="gpt-4",
            temperature=0.5,
            system_prompt="You are a helpful assistant.",
        )
        child = AgentSpec(
            name="child-agent",
            provider="openai",
            model="gpt-3.5-turbo",
            parent="base-agent",
        )

        specs = {"base-agent": base, "child-agent": child}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        agent = factory.create(child)

        # Child values override
        assert agent.spec.name == "child-agent"
        assert agent.spec.model == "gpt-3.5-turbo"

        # Parent values inherited
        assert agent.spec.system_prompt == "You are a helpful assistant."
        assert agent.spec.temperature == 0.5

    def test_create_agent_with_tools_merge(self):
        """Test that tools are merged additively."""
        base = AgentSpec(
            name="base-agent",
            provider="openai",
            model="gpt-4",
            tools=["read_file", "write_file"],
        )
        child = AgentSpec(
            name="child-agent",
            provider="openai",
            model="gpt-4",
            parent="base-agent",
            tools=["execute_code"],
        )

        specs = {"base-agent": base}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        agent = factory.create(child)

        # Tools should be merged
        assert set(agent.spec.tools) == {"read_file", "write_file", "execute_code"}

    def test_create_agent_with_metadata_merge(self):
        """Test that metadata is merged with child overriding parent."""
        base = AgentSpec(
            name="base-agent",
            provider="openai",
            model="gpt-4",
            metadata={"team": "platform", "version": "1.0"},
        )
        child = AgentSpec(
            name="child-agent",
            provider="openai",
            model="gpt-4",
            parent="base-agent",
            metadata={"version": "2.0", "author": "john"},
        )

        specs = {"base-agent": base}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        agent = factory.create(child)

        # Metadata merged with child override
        assert agent.spec.metadata == {
            "team": "platform",
            "version": "2.0",
            "author": "john",
        }

    def test_circular_inheritance_raises_error(self):
        """Test that circular inheritance is detected."""
        agent_a = AgentSpec(
            name="agent-a", provider="openai", model="gpt-4", parent="agent-b"
        )
        agent_b = AgentSpec(
            name="agent-b", provider="openai", model="gpt-4", parent="agent-a"
        )

        specs = {"agent-a": agent_a, "agent-b": agent_b}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)

        with pytest.raises(CircularInheritanceError) as exc_info:
            factory.create(agent_a)

        assert "agent-a" in str(exc_info.value)
        assert "agent-b" in str(exc_info.value)

    def test_parent_not_found_raises_error(self):
        """Test that missing parent raises error."""
        child = AgentSpec(
            name="child-agent",
            provider="openai",
            model="gpt-4",
            parent="missing-parent",
        )

        def get_parent(name: str):
            return None

        factory = AgentFactory(get_parent)

        with pytest.raises(ParentNotFoundError) as exc_info:
            factory.create(child)

        assert "missing-parent" in str(exc_info.value)

    def test_max_depth_exceeded_raises_error(self):
        """Test that max depth is enforced."""
        # Create a chain: a -> b -> c -> d -> e -> f (depth 5)
        specs = {}
        for i in range(6):
            name = f"agent-{chr(97 + i)}"
            parent = f"agent-{chr(97 + i + 1)}" if i < 5 else None
            specs[name] = AgentSpec(
                name=name, provider="openai", model="gpt-4", parent=parent
            )

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent, max_inheritance_depth=4)

        with pytest.raises(MaxDepthExceededError) as exc_info:
            factory.create(specs["agent-a"])

        assert "exceeds maximum 4" in str(exc_info.value)

    def test_validate_spec(self):
        """Test validating a spec without creating an agent."""
        # Deep inheritance (3+ levels) should generate warning
        specs = {
            "root": AgentSpec(name="root", provider="openai", model="gpt-4"),
            "level1": AgentSpec(
                name="level1", provider="openai", model="gpt-4", parent="root"
            ),
            "level2": AgentSpec(
                name="level2", provider="openai", model="gpt-4", parent="level1"
            ),
            "level3": AgentSpec(
                name="level3", provider="openai", model="gpt-4", parent="level2"
            ),
        }

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent, warn_depth=3)
        warnings = factory.validate_spec(specs["level3"])

        assert len(warnings) > 0
        assert "warning threshold" in warnings[0].lower()

    def test_get_inheritance_chain(self):
        """Test getting the inheritance chain."""
        specs = {
            "root": AgentSpec(name="root", provider="openai", model="gpt-4"),
            "middle": AgentSpec(
                name="middle", provider="openai", model="gpt-4", parent="root"
            ),
            "leaf": AgentSpec(
                name="leaf", provider="openai", model="gpt-4", parent="middle"
            ),
        }

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        chain = factory.get_inheritance_chain(specs["leaf"])

        assert chain == ["leaf", "middle", "root"]

    def test_preview_resolved_spec(self):
        """Test previewing resolved spec without creating agent."""
        base = AgentSpec(
            name="base-agent",
            provider="openai",
            model="gpt-4",
            temperature=0.5,
            system_prompt="Base prompt",
        )
        child = AgentSpec(
            name="child-agent",
            provider="openai",
            model="gpt-3.5-turbo",
            parent="base-agent",
        )

        specs = {"base-agent": base}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        resolved = factory.preview_resolved_spec(child)

        assert resolved.name == "child-agent"
        assert resolved.model == "gpt-3.5-turbo"
        assert resolved.system_prompt == "Base prompt"
        assert resolved.temperature == 0.5

    def test_create_with_provider(self):
        """Test creating an agent with provider instance."""
        spec = AgentSpec(name="test-agent", provider="openai", model="gpt-4")

        def get_parent(name: str):
            return None

        factory = AgentFactory(get_parent, provider_registry=MockProviderRegistry)
        agent, provider = factory.create_with_provider(spec)

        assert agent.spec.name == "test-agent"
        assert provider == "Provider:openai"

    def test_create_with_provider_unavailable(self):
        """Test error when provider is not available."""
        spec = AgentSpec(name="test-agent", provider="unknown", model="gpt-4")

        def get_parent(name: str):
            return None

        factory = AgentFactory(get_parent, provider_registry=MockProviderRegistry)

        with pytest.raises(ProviderNotAvailableError) as exc_info:
            factory.create_with_provider(spec)

        assert "unknown" in str(exc_info.value)
        assert "openai" in str(exc_info.value)  # Available provider

    def test_create_with_provider_no_registry(self):
        """Test error when provider registry is not configured."""
        spec = AgentSpec(name="test-agent", provider="openai", model="gpt-4")

        def get_parent(name: str):
            return None

        factory = AgentFactory(get_parent)  # No provider registry

        with pytest.raises(ValueError, match="Provider registry not configured"):
            factory.create_with_provider(spec)

    def test_create_with_provider_config(self):
        """Test creating provider with custom config."""
        spec = AgentSpec(name="test-agent", provider="anthropic", model="claude-3")

        def get_parent(name: str):
            return None

        factory = AgentFactory(get_parent, provider_registry=MockProviderRegistry)
        agent, provider = factory.create_with_provider(
            spec, provider_config={"api_key": "test-key", "timeout": 30}
        )

        assert agent.spec.name == "test-agent"
        assert provider == "Provider:anthropic"

    def test_inheritance_metadata_attached(self):
        """Test that inheritance metadata is attached to agent."""
        base = AgentSpec(name="base-agent", provider="openai", model="gpt-4")
        child = AgentSpec(
            name="child-agent",
            provider="openai",
            model="gpt-4",
            parent="base-agent",
        )

        specs = {"base-agent": base}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        agent = factory.create(child)

        # Check metadata is attached
        assert hasattr(agent, "_inheritance_chain")
        assert hasattr(agent, "_inheritance_depth")
        assert hasattr(agent, "_inheritance_warnings")

        assert agent._inheritance_chain == ["child-agent", "base-agent"]  # type: ignore
        assert agent._inheritance_depth == 1  # type: ignore

    def test_multi_level_inheritance(self):
        """Test multi-level inheritance (grandparent -> parent -> child)."""
        grandparent = AgentSpec(
            name="grandparent",
            provider="openai",
            model="gpt-4",
            temperature=0.3,
            system_prompt="Grandparent prompt",
            tools=["tool1"],
            metadata={"level": "grandparent"},
        )
        parent = AgentSpec(
            name="parent",
            provider="openai",
            model="gpt-4",
            parent="grandparent",
            temperature=0.5,
            tools=["tool2"],
            metadata={"level": "parent", "extra": "data"},
        )
        child = AgentSpec(
            name="child",
            provider="openai",
            model="gpt-3.5-turbo",
            parent="parent",
            tools=["tool3"],
            metadata={"level": "child"},
        )

        specs = {"grandparent": grandparent, "parent": parent}

        def get_parent(name: str):
            return specs.get(name)

        factory = AgentFactory(get_parent)
        agent = factory.create(child)

        # Child overrides
        assert agent.spec.name == "child"
        assert agent.spec.model == "gpt-3.5-turbo"
        assert agent.spec.metadata["level"] == "child"

        # Parent overrides grandparent
        assert agent.spec.temperature == 0.5

        # Grandparent values inherited
        assert agent.spec.system_prompt == "Grandparent prompt"

        # Tools merged from all levels
        assert set(agent.spec.tools) == {"tool1", "tool2", "tool3"}

        # Metadata merged with proper override
        assert agent.spec.metadata["extra"] == "data"  # from parent
        assert agent.spec.metadata["level"] == "child"  # child overrides
