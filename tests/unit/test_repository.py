"""Tests for repository pattern implementation."""

import pytest

from paracle_domain import Agent, AgentSpec, EntityStatus, Tool, ToolSpec
from paracle_store import (
    AgentRepository,
    DuplicateError,
    InMemoryRepository,
    NotFoundError,
    ToolRepository,
    WorkflowRepository,
)
from paracle_domain import Workflow, WorkflowSpec, WorkflowStep


class TestInMemoryRepository:
    """Tests for base InMemoryRepository."""

    def test_add_and_get(self) -> None:
        """Test adding and getting an entity."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        repo.add(agent)
        retrieved = repo.get(agent.id)

        assert retrieved is not None
        assert retrieved.id == agent.id

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent entity returns None."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        assert repo.get("nonexistent") is None

    def test_get_or_raise(self) -> None:
        """Test get_or_raise raises for nonexistent."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        with pytest.raises(NotFoundError) as exc_info:
            repo.get_or_raise("nonexistent")

        assert exc_info.value.entity_type == "Agent"
        assert exc_info.value.entity_id == "nonexistent"

    def test_add_duplicate(self) -> None:
        """Test adding duplicate raises error."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(id="fixed_id", spec=spec)
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        repo.add(agent)
        with pytest.raises(DuplicateError):
            repo.add(agent)

    def test_list(self) -> None:
        """Test listing all entities."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        for i in range(3):
            spec = AgentSpec(name=f"agent-{i}", provider="openai", model="gpt-4")
            repo.add(Agent(spec=spec))

        agents = repo.list()
        assert len(agents) == 3

    def test_update(self) -> None:
        """Test updating an entity."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        repo.add(agent)
        agent.update_status(phase=EntityStatus.RUNNING)
        repo.update(agent)

        retrieved = repo.get(agent.id)
        assert retrieved is not None
        assert retrieved.status.phase == EntityStatus.RUNNING

    def test_update_nonexistent(self) -> None:
        """Test updating nonexistent raises error."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        with pytest.raises(NotFoundError):
            repo.update(agent)

    def test_delete(self) -> None:
        """Test deleting an entity."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        repo.add(agent)
        assert repo.delete(agent.id) is True
        assert repo.get(agent.id) is None

    def test_delete_nonexistent(self) -> None:
        """Test deleting nonexistent returns False."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        assert repo.delete("nonexistent") is False

    def test_exists(self) -> None:
        """Test exists method."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        assert not repo.exists(agent.id)
        repo.add(agent)
        assert repo.exists(agent.id)

    def test_count(self) -> None:
        """Test counting entities."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        assert repo.count() == 0
        for i in range(5):
            spec = AgentSpec(name=f"agent-{i}", provider="openai", model="gpt-4")
            repo.add(Agent(spec=spec))
        assert repo.count() == 5

    def test_clear(self) -> None:
        """Test clearing all entities."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        for i in range(3):
            spec = AgentSpec(name=f"agent-{i}", provider="openai", model="gpt-4")
            repo.add(Agent(spec=spec))

        cleared = repo.clear()
        assert cleared == 3
        assert repo.count() == 0

    def test_find_by(self) -> None:
        """Test finding by predicate."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        for i in range(5):
            spec = AgentSpec(name=f"agent-{i}", provider="openai", model="gpt-4")
            agent = Agent(spec=spec)
            if i >= 3:
                agent.update_status(phase=EntityStatus.RUNNING)
            repo.add(agent)

        running = repo.find_by(lambda a: a.status.phase == EntityStatus.RUNNING)
        assert len(running) == 2

    def test_find_one_by(self) -> None:
        """Test finding one by predicate."""
        repo: InMemoryRepository[Agent] = InMemoryRepository(
            entity_type="Agent",
            id_getter=lambda a: a.id,
        )

        spec = AgentSpec(name="target", provider="openai", model="gpt-4")
        repo.add(Agent(spec=spec))
        spec2 = AgentSpec(name="other", provider="openai", model="gpt-4")
        repo.add(Agent(spec=spec2))

        found = repo.find_one_by(lambda a: a.spec.name == "target")
        assert found is not None
        assert found.spec.name == "target"

        not_found = repo.find_one_by(lambda a: a.spec.name == "nonexistent")
        assert not_found is None


class TestAgentRepository:
    """Tests for AgentRepository."""

    def test_register_and_get_spec(self) -> None:
        """Test registering and getting specs."""
        repo = AgentRepository()
        spec = AgentSpec(name="test-agent", provider="openai", model="gpt-4")

        repo.register_spec(spec)
        retrieved = repo.get_spec("test-agent")

        assert retrieved is not None
        assert retrieved.name == "test-agent"

    def test_list_specs(self) -> None:
        """Test listing specs."""
        repo = AgentRepository()
        for i in range(3):
            spec = AgentSpec(name=f"agent-{i}", provider="openai", model="gpt-4")
            repo.register_spec(spec)

        specs = repo.list_specs()
        assert len(specs) == 3

    def test_remove_spec(self) -> None:
        """Test removing a spec."""
        repo = AgentRepository()
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        repo.register_spec(spec)

        assert repo.remove_spec("test") is True
        assert repo.get_spec("test") is None
        assert repo.remove_spec("nonexistent") is False

    def test_create_from_spec(self) -> None:
        """Test creating agent from spec."""
        repo = AgentRepository()
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        repo.register_spec(spec)

        agent = repo.create_from_spec("test")

        assert agent.spec.name == "test"
        assert repo.exists(agent.id)

    def test_create_from_nonexistent_spec(self) -> None:
        """Test creating from nonexistent spec raises error."""
        repo = AgentRepository()

        with pytest.raises(ValueError, match="not found"):
            repo.create_from_spec("nonexistent")

    def test_find_by_status(self) -> None:
        """Test finding by status."""
        repo = AgentRepository()

        for i in range(4):
            spec = AgentSpec(name=f"agent-{i}", provider="openai", model="gpt-4")
            agent = Agent(spec=spec)
            if i % 2 == 0:
                agent.update_status(phase=EntityStatus.RUNNING)
            repo.add(agent)

        running = repo.find_by_status(EntityStatus.RUNNING)
        assert len(running) == 2

    def test_find_active(self) -> None:
        """Test finding active agents."""
        repo = AgentRepository()

        spec = AgentSpec(name="active", provider="openai", model="gpt-4")
        active = Agent(spec=spec)
        active.update_status(phase=EntityStatus.ACTIVE)
        repo.add(active)

        spec2 = AgentSpec(name="running", provider="openai", model="gpt-4")
        running = Agent(spec=spec2)
        running.update_status(phase=EntityStatus.RUNNING)
        repo.add(running)

        spec3 = AgentSpec(name="pending", provider="openai", model="gpt-4")
        repo.add(Agent(spec=spec3))

        found = repo.find_active()
        assert len(found) == 2

    def test_find_by_provider(self) -> None:
        """Test finding by provider."""
        repo = AgentRepository()

        repo.add(
            Agent(spec=AgentSpec(name="a1", provider="openai", model="gpt-4"))
        )
        repo.add(
            Agent(spec=AgentSpec(name="a2", provider="anthropic", model="claude"))
        )
        repo.add(
            Agent(spec=AgentSpec(name="a3", provider="openai", model="gpt-3.5"))
        )

        openai_agents = repo.find_by_provider("openai")
        assert len(openai_agents) == 2


class TestWorkflowRepository:
    """Tests for WorkflowRepository."""

    def test_create_from_spec(self) -> None:
        """Test creating workflow from spec."""
        repo = WorkflowRepository()
        spec = WorkflowSpec(
            name="test-workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent="agent-1")],
        )
        repo.register_spec(spec)

        workflow = repo.create_from_spec("test-workflow")

        assert workflow.spec.name == "test-workflow"
        assert repo.exists(workflow.id)

    def test_find_running(self) -> None:
        """Test finding running workflows."""
        repo = WorkflowRepository()
        spec = WorkflowSpec(
            name="wf",
            steps=[WorkflowStep(id="s1", name="Step 1", agent="a1")],
        )
        repo.register_spec(spec)

        for _ in range(3):
            wf = repo.create_from_spec("wf")
            wf.start()
            repo.update(wf)

        # Add a completed one
        wf = repo.create_from_spec("wf")
        wf.start()
        wf.complete()
        repo.update(wf)

        running = repo.find_running()
        assert len(running) == 3


class TestToolRepository:
    """Tests for ToolRepository."""

    def test_register_and_find_by_name(self) -> None:
        """Test registering and finding tools by name."""
        repo = ToolRepository()
        spec = ToolSpec(name="read_file", description="Reads a file")

        tool = repo.register(spec)
        found = repo.find_by_name("read_file")

        assert found is not None
        assert found.id == tool.id

    def test_find_enabled(self) -> None:
        """Test finding enabled tools."""
        repo = ToolRepository()

        for i in range(3):
            spec = ToolSpec(name=f"tool-{i}", description=f"Tool {i}")
            repo.register(spec)

        # Disable one
        tools = repo.list()
        repo.disable(tools[0].id)

        enabled = repo.find_enabled()
        assert len(enabled) == 2

    def test_find_mcp_tools(self) -> None:
        """Test finding MCP tools."""
        repo = ToolRepository()

        repo.register(ToolSpec(name="internal", description="Internal tool"))
        repo.register(
            ToolSpec(
                name="mcp1",
                description="MCP tool",
                is_mcp=True,
                mcp_server="http://localhost:3000",
            )
        )
        repo.register(
            ToolSpec(
                name="mcp2",
                description="Another MCP tool",
                is_mcp=True,
                mcp_server="http://localhost:3001",
            )
        )

        mcp = repo.find_mcp_tools()
        internal = repo.find_internal_tools()

        assert len(mcp) == 2
        assert len(internal) == 1

    def test_enable_disable(self) -> None:
        """Test enabling and disabling tools."""
        repo = ToolRepository()
        spec = ToolSpec(name="test", description="Test tool")
        tool = repo.register(spec)

        assert repo.disable(tool.id) is True
        assert repo.get(tool.id).enabled is False

        assert repo.enable(tool.id) is True
        assert repo.get(tool.id).enabled is True

        assert repo.disable("nonexistent") is False
        assert repo.enable("nonexistent") is False
