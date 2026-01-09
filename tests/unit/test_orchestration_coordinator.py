"""Tests for AgentCoordinator."""

import pytest

from paracle_domain.factory import AgentFactory
from paracle_domain.models import Agent, AgentSpec
from paracle_orchestration.coordinator import AgentCoordinator


@pytest.fixture
def spec_provider():
    """Create a spec provider for testing."""
    specs = {}

    def get_spec(name: str) -> AgentSpec | None:
        return specs.get(name)

    # Add a base agent
    base_spec = AgentSpec(
        name="base-agent",
        provider="openai",
        model="gpt-4",
        temperature=0.7,
        system_prompt="Base agent",
    )
    specs[base_spec.name] = base_spec

    return get_spec


@pytest.fixture
def agent_factory(spec_provider):
    """Create an agent factory."""
    return AgentFactory(spec_provider)


@pytest.fixture
def coordinator(agent_factory):
    """Create an agent coordinator."""
    return AgentCoordinator(agent_factory)


@pytest.fixture
def test_agent():
    """Create a test agent."""
    spec = AgentSpec(
        name="test-agent", provider="openai", model="gpt-4", temperature=0.5
    )
    return Agent(spec=spec)


class TestAgentCoordinatorCreation:
    """Test AgentCoordinator initialization."""

    def test_create_coordinator_with_defaults(self, agent_factory):
        # Arrange & Act
        coordinator = AgentCoordinator(agent_factory)

        # Assert
        assert coordinator.cache_enabled is True
        assert coordinator.max_cache_size == 100
        assert len(coordinator.agent_cache) == 0
        assert len(coordinator.execution_metrics) == 0

    def test_create_coordinator_with_custom_settings(self, agent_factory):
        # Arrange & Act
        coordinator = AgentCoordinator(
            agent_factory, cache_enabled=False, max_cache_size=50
        )

        # Assert
        assert coordinator.cache_enabled is False
        assert coordinator.max_cache_size == 50


class TestAgentExecution:
    """Test agent execution."""

    @pytest.mark.asyncio
    async def test_execute_agent_returns_result(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello", "data": "world"}

        # Act
        result = await coordinator.execute_agent(test_agent, inputs)

        # Assert
        assert "agent_id" in result
        assert result["agent_id"] == test_agent.id
        assert "result" in result
        assert "execution_time" in result
        assert "metadata" in result
        assert result["metadata"]["agent_name"] == "test-agent"
        assert result["metadata"]["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_execute_agent_with_context(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello"}
        context = {"user": "alice", "session": "123"}

        # Act
        result = await coordinator.execute_agent(test_agent, inputs, context)

        # Assert
        assert result is not None
        assert result["agent_id"] == test_agent.id

    @pytest.mark.asyncio
    async def test_execute_agent_tracks_metrics(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello"}

        # Act
        await coordinator.execute_agent(test_agent, inputs)

        # Assert
        metrics = coordinator.get_metrics(test_agent.id)
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["failed_executions"] == 0
        assert metrics["total_execution_time"] > 0
        assert metrics["avg_execution_time"] > 0

    @pytest.mark.asyncio
    async def test_execute_agent_multiple_times_updates_metrics(
        self, coordinator, test_agent
    ):
        # Arrange
        inputs = {"task": "hello"}

        # Act
        await coordinator.execute_agent(test_agent, inputs)
        await coordinator.execute_agent(test_agent, inputs)
        await coordinator.execute_agent(test_agent, inputs)

        # Assert
        metrics = coordinator.get_metrics(test_agent.id)
        assert metrics["total_executions"] == 3
        assert metrics["successful_executions"] == 3


class TestAgentCaching:
    """Test agent caching."""

    @pytest.mark.asyncio
    async def test_agent_cached_after_first_execution(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello"}

        # Act
        await coordinator.execute_agent(test_agent, inputs)

        # Assert
        assert test_agent.id in coordinator.agent_cache

    @pytest.mark.asyncio
    async def test_cached_agent_reused(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello"}

        # Act
        await coordinator.execute_agent(test_agent, inputs)
        first_instance = coordinator.agent_cache[test_agent.id]

        await coordinator.execute_agent(test_agent, inputs)
        second_instance = coordinator.agent_cache[test_agent.id]

        # Assert
        assert first_instance is second_instance

    @pytest.mark.asyncio
    async def test_cache_disabled_does_not_cache(self, agent_factory, test_agent):
        # Arrange
        coordinator = AgentCoordinator(agent_factory, cache_enabled=False)
        inputs = {"task": "hello"}

        # Act
        await coordinator.execute_agent(test_agent, inputs)

        # Assert
        assert len(coordinator.agent_cache) == 0

    @pytest.mark.asyncio
    async def test_cache_eviction_when_limit_exceeded(self, agent_factory):
        # Arrange
        coordinator = AgentCoordinator(agent_factory, max_cache_size=2)

        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agent2 = Agent(spec=AgentSpec(name="agent2", provider="openai", model="gpt-4"))
        agent3 = Agent(spec=AgentSpec(name="agent3", provider="openai", model="gpt-4"))

        inputs = {"task": "hello"}

        # Act
        await coordinator.execute_agent(agent1, inputs)
        await coordinator.execute_agent(agent2, inputs)
        await coordinator.execute_agent(agent3, inputs)

        # Assert
        assert len(coordinator.agent_cache) == 2
        assert agent1.id not in coordinator.agent_cache  # Evicted (oldest)
        assert agent2.id in coordinator.agent_cache
        assert agent3.id in coordinator.agent_cache


class TestParallelExecution:
    """Test parallel agent execution."""

    @pytest.mark.asyncio
    async def test_execute_parallel_with_multiple_agents(self, coordinator):
        # Arrange
        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agent2 = Agent(spec=AgentSpec(name="agent2", provider="openai", model="gpt-4"))
        agent3 = Agent(spec=AgentSpec(name="agent3", provider="openai", model="gpt-4"))

        agents = [agent1, agent2, agent3]
        inputs_list = [{"task": "a"}, {"task": "b"}, {"task": "c"}]

        # Act
        results = await coordinator.execute_parallel(agents, inputs_list)

        # Assert
        assert len(results) == 3
        assert all("result" in r for r in results)
        assert results[0]["agent_id"] == agent1.id
        assert results[1]["agent_id"] == agent2.id
        assert results[2]["agent_id"] == agent3.id

    @pytest.mark.asyncio
    async def test_execute_parallel_with_shared_context(self, coordinator):
        # Arrange
        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agent2 = Agent(spec=AgentSpec(name="agent2", provider="openai", model="gpt-4"))

        agents = [agent1, agent2]
        inputs_list = [{"task": "a"}, {"task": "b"}]
        shared_context = {"user": "alice", "session": "123"}

        # Act
        results = await coordinator.execute_parallel(
            agents, inputs_list, shared_context
        )

        # Assert
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_raises_for_mismatched_lengths(self, coordinator):
        # Arrange
        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agents = [agent1]
        inputs_list = [{"task": "a"}, {"task": "b"}]  # Different length

        # Act & Assert
        with pytest.raises(ValueError, match="does not match"):
            await coordinator.execute_parallel(agents, inputs_list)

    @pytest.mark.asyncio
    async def test_execute_parallel_handles_exceptions(self, coordinator, mocker):
        # Arrange
        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agent2 = Agent(spec=AgentSpec(name="agent2", provider="openai", model="gpt-4"))

        agents = [agent1, agent2]
        inputs_list = [{"task": "a"}, {"task": "b"}]

        # Mock the execution to raise exception for first agent
        async def mock_execute(agent, inputs, context=None):
            if agent.id == agent1.id:
                raise ValueError("Test error")
            return {
                "agent_id": agent.id,
                "result": {"echo": inputs},
                "execution_time": 0.1,
                "metadata": {},
            }

        coordinator.execute_agent = mock_execute

        # Act
        results = await coordinator.execute_parallel(agents, inputs_list)

        # Assert
        assert len(results) == 2
        assert results[0]["success"] is False
        assert "error" in results[0]
        assert "result" in results[1]


class TestCacheManagement:
    """Test cache management operations."""

    @pytest.mark.asyncio
    async def test_clear_cache_all(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello"}
        await coordinator.execute_agent(test_agent, inputs)
        assert len(coordinator.agent_cache) == 1

        # Act
        coordinator.clear_cache()

        # Assert
        assert len(coordinator.agent_cache) == 0

    @pytest.mark.asyncio
    async def test_clear_cache_specific_agent(self, coordinator):
        # Arrange
        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agent2 = Agent(spec=AgentSpec(name="agent2", provider="openai", model="gpt-4"))

        inputs = {"task": "hello"}
        await coordinator.execute_agent(agent1, inputs)
        await coordinator.execute_agent(agent2, inputs)

        assert len(coordinator.agent_cache) == 2

        # Act
        coordinator.clear_cache(agent1.id)

        # Assert
        assert len(coordinator.agent_cache) == 1
        assert agent1.id not in coordinator.agent_cache
        assert agent2.id in coordinator.agent_cache

    def test_get_cache_stats(self, coordinator):
        # Act
        stats = coordinator.get_cache_stats()

        # Assert
        assert "cached_agents" in stats
        assert "cache_size_limit" in stats
        assert "cache_enabled" in stats
        assert stats["cached_agents"] == 0
        assert stats["cache_size_limit"] == 100
        assert stats["cache_enabled"] is True


class TestMetrics:
    """Test metrics collection."""

    @pytest.mark.asyncio
    async def test_get_metrics_for_specific_agent(self, coordinator, test_agent):
        # Arrange
        inputs = {"task": "hello"}
        await coordinator.execute_agent(test_agent, inputs)

        # Act
        metrics = coordinator.get_metrics(test_agent.id)

        # Assert
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["failed_executions"] == 0
        assert metrics["total_execution_time"] > 0
        assert metrics["avg_execution_time"] > 0

    @pytest.mark.asyncio
    async def test_get_metrics_for_all_agents(self, coordinator):
        # Arrange
        agent1 = Agent(spec=AgentSpec(name="agent1", provider="openai", model="gpt-4"))
        agent2 = Agent(spec=AgentSpec(name="agent2", provider="openai", model="gpt-4"))

        inputs = {"task": "hello"}
        await coordinator.execute_agent(agent1, inputs)
        await coordinator.execute_agent(agent2, inputs)

        # Act
        all_metrics = coordinator.get_metrics()

        # Assert
        assert len(all_metrics) == 2
        assert agent1.id in all_metrics
        assert agent2.id in all_metrics

    def test_get_metrics_for_nonexistent_agent(self, coordinator):
        # Act
        metrics = coordinator.get_metrics("nonexistent_id")

        # Assert
        assert metrics == {}
