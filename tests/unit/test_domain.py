"""Unit tests for domain models."""

import pytest
from paracle_domain.models import AgentSpec, Agent, EntityStatus


class TestAgentSpec:
    """Tests for AgentSpec model."""

    def test_agent_spec_creation(self, sample_agent_spec: dict) -> None:
        """Test creating an agent spec with valid data."""
        spec = AgentSpec(**sample_agent_spec)
        assert spec.name == "test-agent"
        assert spec.provider == "openai"
        assert spec.model == "gpt-4"
        assert spec.temperature == 0.7

    def test_agent_spec_temperature_validation(self) -> None:
        """Test temperature validation."""
        with pytest.raises(ValueError):
            AgentSpec(
                name="test",
                provider="openai",
                model="gpt-4",
                temperature=3.0,  # Invalid: > 2.0
            )

    def test_agent_spec_defaults(self) -> None:
        """Test default values."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        assert spec.temperature == 0.7  # Default
        assert spec.max_tokens is None  # Default
        assert spec.system_prompt is None  # Default


class TestAgent:
    """Tests for Agent model."""

    def test_agent_creation(self, sample_agent_spec: dict) -> None:
        """Test creating an agent."""
        spec = AgentSpec(**sample_agent_spec)
        agent = Agent(spec=spec)
        assert agent.id is not None
        assert agent.spec == spec
        assert agent.status.phase == EntityStatus.PENDING

    def test_agent_id_generation(self, sample_agent_spec: dict) -> None:
        """Test that each agent gets a unique ID."""
        spec = AgentSpec(**sample_agent_spec)
        agent1 = Agent(spec=spec)
        agent2 = Agent(spec=spec)
        assert agent1.id != agent2.id
