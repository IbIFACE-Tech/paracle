"""Unit tests for paracle_meta.capabilities.agent_spawner module."""

import pytest

from paracle_meta.capabilities.agent_spawner import (
    AgentPool,
    AgentSpawner,
    AgentStatus,
    AgentType,
    SpawnConfig,
    SpawnedAgent,
)


class TestSpawnConfig:
    """Tests for SpawnConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SpawnConfig()
        assert config.max_spawned_agents == 10
        assert config.agent_idle_timeout == 300.0
        assert config.auto_scale is True
        assert config.scale_up_threshold == 0.8
        assert config.scale_down_threshold == 0.2
        assert config.min_agents == 0
        assert (
            "claude" in config.default_model.lower()
            or "anthropic" in config.default_model.lower()
        )

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SpawnConfig(
            max_spawned_agents=20,
            agent_idle_timeout=600.0,
            auto_scale=False,
            scale_up_threshold=0.9,
            min_agents=2,
        )
        assert config.max_spawned_agents == 20
        assert config.agent_idle_timeout == 600.0
        assert config.auto_scale is False
        assert config.scale_up_threshold == 0.9
        assert config.min_agents == 2


class TestSpawnedAgent:
    """Tests for SpawnedAgent model."""

    def test_create_agent(self):
        """Test creating a spawned agent."""
        agent = SpawnedAgent(
            name="TestAgent",
            agent_type=AgentType.CODER,
            model="gpt-4",
            system_prompt="You are a coder",
        )

        assert agent.name == "TestAgent"
        assert agent.agent_type == AgentType.CODER
        assert agent.model == "gpt-4"
        assert agent.status == AgentStatus.INITIALIZING
        assert agent.id.startswith("agent_")

    def test_agent_defaults(self):
        """Test agent default values."""
        agent = SpawnedAgent(
            name="Simple",
            agent_type=AgentType.GENERAL,
        )

        assert agent.tasks_completed == 0
        assert agent.total_tokens_used == 0
        assert agent.total_cost_usd == 0.0
        assert agent.current_task is None
        assert agent.capabilities == []

    def test_agent_is_available(self):
        """Test is_available property."""
        agent = SpawnedAgent(name="Test", agent_type=AgentType.GENERAL)

        # Initializing - not available
        agent.status = AgentStatus.INITIALIZING
        assert agent.is_available is False

        # Ready - available
        agent.status = AgentStatus.READY
        assert agent.is_available is True

        # Idle - available
        agent.status = AgentStatus.IDLE
        assert agent.is_available is True

        # Busy - not available
        agent.status = AgentStatus.BUSY
        assert agent.is_available is False

        # Terminated - not available
        agent.status = AgentStatus.TERMINATED
        assert agent.is_available is False


class TestAgentPool:
    """Tests for AgentPool."""

    @pytest.fixture
    def pool(self):
        """Create agent pool instance."""
        config = SpawnConfig(max_spawned_agents=5)
        return AgentPool(config)

    @pytest.mark.asyncio
    async def test_add_and_remove_agent(self, pool):
        """Test adding and removing agents."""
        agent = SpawnedAgent(name="Test", agent_type=AgentType.GENERAL)
        agent.status = AgentStatus.READY

        # Add agent
        await pool.add_agent(agent)
        assert pool.total_agents == 1
        assert pool.available_agents == 1

        # Remove agent
        removed = await pool.remove_agent(agent.id)
        assert removed is not None
        assert removed.id == agent.id
        assert pool.total_agents == 0

    @pytest.mark.asyncio
    async def test_get_available_agent(self, pool):
        """Test getting available agent."""
        # Add some agents
        agent1 = SpawnedAgent(name="Agent1", agent_type=AgentType.CODER)
        agent1.status = AgentStatus.BUSY

        agent2 = SpawnedAgent(name="Agent2", agent_type=AgentType.REVIEWER)
        agent2.status = AgentStatus.READY

        await pool.add_agent(agent1)
        await pool.add_agent(agent2)

        # Get any available
        available = await pool.get_available_agent()
        assert available is not None
        assert available.id == agent2.id

        # Get specific type
        available = await pool.get_available_agent(AgentType.REVIEWER)
        assert available is not None
        assert available.agent_type == AgentType.REVIEWER

        # Get unavailable type
        available = await pool.get_available_agent(AgentType.TESTER)
        assert available is None

    def test_load_calculation(self, pool):
        """Test load calculation."""
        # Empty pool - full load
        assert pool.load == 1.0

    @pytest.mark.asyncio
    async def test_load_with_agents(self, pool):
        """Test load with agents."""
        agent1 = SpawnedAgent(name="Agent1", agent_type=AgentType.GENERAL)
        agent1.status = AgentStatus.BUSY

        agent2 = SpawnedAgent(name="Agent2", agent_type=AgentType.GENERAL)
        agent2.status = AgentStatus.READY

        await pool.add_agent(agent1)
        await pool.add_agent(agent2)

        # 1 busy out of 2 = 50% load
        assert pool.load == 0.5


class TestAgentSpawner:
    """Tests for AgentSpawner."""

    @pytest.fixture
    def spawner(self):
        """Create agent spawner instance."""
        config = SpawnConfig(
            max_spawned_agents=5,
            auto_scale=False,  # Disable for testing
        )
        return AgentSpawner(config=config)

    def test_initialization(self, spawner):
        """Test capability initialization."""
        assert spawner.name == "agent_spawner"
        assert "spawn" in spawner.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, spawner):
        """Test initialize and shutdown lifecycle."""
        await spawner.initialize()
        assert spawner.is_initialized is True
        assert spawner._pool is not None

        await spawner.shutdown()
        assert spawner.is_initialized is False

    @pytest.mark.asyncio
    async def test_spawn_agent(self, spawner):
        """Test spawning an agent."""
        await spawner.initialize()

        result = await spawner.spawn(
            name="TestAgent",
            agent_type="coder",
            capabilities=["code_review"],
        )

        assert result.success is True
        assert result.output["name"] == "TestAgent"
        assert result.output["agent_type"] == "coder"
        assert result.output["status"] == "ready"
        assert "code_review" in result.output["capabilities"]

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_spawn_max_agents(self, spawner):
        """Test spawning up to max agents."""
        await spawner.initialize()

        # Spawn max agents
        for i in range(5):
            result = await spawner.spawn(name=f"Agent{i}", agent_type="general")
            assert result.success is True

        # Try to spawn one more - should fail
        result = await spawner.spawn(name="ExtraAgent", agent_type="general")
        assert result.success is False
        assert "maximum" in result.error.lower()

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_terminate_agent(self, spawner):
        """Test terminating an agent."""
        await spawner.initialize()

        # Spawn an agent
        spawn_result = await spawner.spawn(name="ToTerminate", agent_type="general")
        agent_id = spawn_result.output["id"]

        # Terminate it
        term_result = await spawner.terminate(agent_id)

        assert term_result.success is True
        assert term_result.output["terminated"] is True

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_assign_task(self, spawner):
        """Test assigning a task to an agent."""
        await spawner.initialize()

        # Spawn an agent
        spawn_result = await spawner.spawn(name="Worker", agent_type="general")
        agent_id = spawn_result.output["id"]

        # Assign a task
        assign_result = await spawner.assign(agent_id, "Process data")

        assert assign_result.success is True
        assert assign_result.output["assigned"] is True
        assert assign_result.output["task"] == "Process data"

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_complete_task(self, spawner):
        """Test completing a task."""
        await spawner.initialize()

        # Spawn and assign
        spawn_result = await spawner.spawn(name="Worker", agent_type="general")
        agent_id = spawn_result.output["id"]
        await spawner.assign(agent_id, "Test task")

        # Complete the task
        complete_result = await spawner.execute(
            action="complete_task",
            agent_id=agent_id,
            result={"output": "done"},
            tokens_used=100,
            cost_usd=0.01,
        )

        assert complete_result.success is True
        assert complete_result.output["completed"] is True

        # Check agent stats
        get_result = await spawner.execute(action="get_agent", agent_id=agent_id)
        assert get_result.output["tasks_completed"] == 1
        assert get_result.output["total_tokens_used"] == 100

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_pool_status(self, spawner):
        """Test getting pool status."""
        await spawner.initialize()

        # Spawn some agents
        await spawner.spawn(name="Agent1", agent_type="general")
        await spawner.spawn(name="Agent2", agent_type="general")

        # Get status
        status_result = await spawner.get_pool_status()

        assert status_result.success is True
        assert status_result.output["total_agents"] == 2
        assert status_result.output["available_agents"] == 2
        assert status_result.output["busy_agents"] == 0
        assert status_result.output["load"] == 0.0

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, spawner):
        """Test execute with unknown action."""
        await spawner.initialize()

        result = await spawner.execute(action="unknown_action")

        assert result.success is False
        assert "Unknown action" in result.error

        await spawner.shutdown()

    @pytest.mark.asyncio
    async def test_list_agents(self, spawner):
        """Test listing agents."""
        await spawner.initialize()

        # Spawn agents of different types
        await spawner.spawn(name="Coder1", agent_type="coder")
        await spawner.spawn(name="Reviewer1", agent_type="reviewer")
        await spawner.spawn(name="Coder2", agent_type="coder")

        # List all
        result = await spawner.execute(action="list_agents")
        assert len(result.output) == 3

        # Filter by type
        result = await spawner.execute(action="list_agents", agent_type="coder")
        assert len(result.output) == 2
        assert all(a["agent_type"] == "coder" for a in result.output)

        await spawner.shutdown()

    def test_default_prompts(self, spawner):
        """Test default system prompts exist for all agent types."""
        for agent_type in AgentType:
            assert agent_type in spawner.DEFAULT_PROMPTS
            assert len(spawner.DEFAULT_PROMPTS[agent_type]) > 0

    @pytest.mark.asyncio
    async def test_pool_load_property(self, spawner):
        """Test pool_load property."""
        await spawner.initialize()

        # Empty pool - full load (1.0)
        assert spawner.pool_load == 1.0

        # Add available agents
        await spawner.spawn(name="Agent1", agent_type="general")
        await spawner.spawn(name="Agent2", agent_type="general")

        # 0 busy / 2 total = 0 load
        assert spawner.pool_load == 0.0

        await spawner.shutdown()


class TestAgentSpawnerIntegration:
    """Integration-style tests for AgentSpawner."""

    @pytest.fixture
    def spawner(self):
        """Create spawner for tests."""
        return AgentSpawner(
            config=SpawnConfig(
                max_spawned_agents=10,
                auto_scale=False,
            )
        )

    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self, spawner):
        """Test full agent lifecycle."""
        await spawner.initialize()

        # 1. Spawn agent
        spawn_result = await spawner.spawn(
            name="FullLifecycleAgent",
            agent_type="coder",
            capabilities=["python", "testing"],
        )
        assert spawn_result.success
        agent_id = spawn_result.output["id"]

        # 2. Check status
        status = await spawner.get_pool_status()
        assert status.output["total_agents"] == 1
        assert status.output["available_agents"] == 1

        # 3. Assign task
        assign_result = await spawner.assign(agent_id, "Write unit tests")
        assert assign_result.success

        # 4. Check agent is busy
        status = await spawner.get_pool_status()
        assert status.output["busy_agents"] == 1

        # 5. Complete task
        complete_result = await spawner.execute(
            action="complete_task",
            agent_id=agent_id,
            result={"tests": 5},
            tokens_used=500,
        )
        assert complete_result.success

        # 6. Terminate agent
        term_result = await spawner.terminate(agent_id)
        assert term_result.success
        assert term_result.output["tasks_completed"] == 1

        # 7. Verify pool is empty
        status = await spawner.get_pool_status()
        assert status.output["total_agents"] == 0

        await spawner.shutdown()
