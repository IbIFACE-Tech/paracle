"""Tests for paracle_domain models."""

import pytest
from datetime import datetime, timezone

from paracle_domain import (
    Agent,
    AgentSpec,
    AgentStatus,
    EntityStatus,
    Tool,
    ToolSpec,
    Workflow,
    WorkflowSpec,
    WorkflowStatus,
    WorkflowStep,
)


class TestEntityStatus:
    """Tests for EntityStatus enum."""

    def test_status_values(self) -> None:
        """Test all status values exist."""
        assert EntityStatus.PENDING == "pending"
        assert EntityStatus.ACTIVE == "active"
        assert EntityStatus.RUNNING == "running"
        assert EntityStatus.SUCCEEDED == "succeeded"
        assert EntityStatus.FAILED == "failed"
        assert EntityStatus.ARCHIVED == "archived"


class TestAgentSpec:
    """Tests for AgentSpec model."""

    def test_create_minimal_spec(self) -> None:
        """Test creating a minimal spec."""
        spec = AgentSpec(
            name="test-agent",
            provider="openai",
            model="gpt-4",
        )
        assert spec.name == "test-agent"
        assert spec.provider == "openai"
        assert spec.model == "gpt-4"
        assert spec.temperature == 0.7  # default
        assert spec.parent is None
        assert spec.tools == []

    def test_create_full_spec(self) -> None:
        """Test creating a full spec."""
        spec = AgentSpec(
            name="code-reviewer",
            description="Reviews code for best practices",
            provider="anthropic",
            model="claude-3",
            temperature=0.3,
            max_tokens=4096,
            system_prompt="You are a code reviewer.",
            parent="base-agent",
            tools=["read_file", "write_file"],
            config={"timeout": 30},
            metadata={"team": "engineering"},
        )
        assert spec.name == "code-reviewer"
        assert spec.has_parent()
        assert spec.parent == "base-agent"
        assert len(spec.tools) == 2

    def test_has_parent(self) -> None:
        """Test has_parent method."""
        spec_without_parent = AgentSpec(name="test", provider="openai", model="gpt-4")
        spec_with_parent = AgentSpec(
            name="test", provider="openai", model="gpt-4", parent="base"
        )
        assert not spec_without_parent.has_parent()
        assert spec_with_parent.has_parent()

    def test_temperature_validation(self) -> None:
        """Test temperature must be between 0 and 2."""
        with pytest.raises(ValueError):
            AgentSpec(name="test", provider="openai", model="gpt-4", temperature=-0.1)
        with pytest.raises(ValueError):
            AgentSpec(name="test", provider="openai", model="gpt-4", temperature=2.1)


class TestAgent:
    """Tests for Agent model."""

    def test_create_agent(self) -> None:
        """Test creating an agent."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)

        assert agent.id.startswith("agent_")
        assert agent.spec == spec
        assert agent.resolved_spec is None
        assert agent.status.phase == EntityStatus.PENDING

    def test_get_effective_spec(self) -> None:
        """Test get_effective_spec returns resolved or original."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        resolved = AgentSpec(name="test", provider="openai", model="gpt-4-turbo")

        agent_without_resolved = Agent(spec=spec)
        agent_with_resolved = Agent(spec=spec, resolved_spec=resolved)

        assert agent_without_resolved.get_effective_spec() == spec
        assert agent_with_resolved.get_effective_spec() == resolved

    def test_update_status(self) -> None:
        """Test updating agent status."""
        spec = AgentSpec(name="test", provider="openai", model="gpt-4")
        agent = Agent(spec=spec)

        agent.update_status(phase=EntityStatus.RUNNING, message="Starting")
        assert agent.status.phase == EntityStatus.RUNNING
        assert agent.status.message == "Starting"

        agent.update_status(error="Something went wrong")
        assert agent.status.error == "Something went wrong"


class TestWorkflowStep:
    """Tests for WorkflowStep model."""

    def test_create_step(self) -> None:
        """Test creating a workflow step."""
        step = WorkflowStep(
            id="step-1",
            name="Review Code",
            agent="code-reviewer",
            prompt="Review the following code: {code}",
            depends_on=["step-0"],
        )
        assert step.id == "step-1"
        assert step.agent == "code-reviewer"
        assert "step-0" in step.depends_on


class TestWorkflowSpec:
    """Tests for WorkflowSpec model."""

    def test_create_spec(self) -> None:
        """Test creating a workflow spec."""
        steps = [
            WorkflowStep(id="s1", name="Step 1", agent="agent-1"),
            WorkflowStep(id="s2", name="Step 2", agent="agent-2", depends_on=["s1"]),
        ]
        spec = WorkflowSpec(
            name="code-review-workflow",
            description="Reviews and improves code",
            steps=steps,
        )
        assert spec.name == "code-review-workflow"
        assert len(spec.steps) == 2


class TestWorkflow:
    """Tests for Workflow model."""

    def test_create_workflow(self) -> None:
        """Test creating a workflow."""
        spec = WorkflowSpec(
            name="test-workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent="agent-1")],
        )
        workflow = Workflow(spec=spec)

        assert workflow.id.startswith("workflow_")
        assert workflow.status.phase == EntityStatus.PENDING
        assert workflow.status.progress == 0.0

    def test_start_workflow(self) -> None:
        """Test starting a workflow."""
        spec = WorkflowSpec(
            name="test-workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent="agent-1")],
        )
        workflow = Workflow(spec=spec)
        workflow.start()

        assert workflow.status.phase == EntityStatus.RUNNING
        assert workflow.status.started_at is not None

    def test_complete_workflow(self) -> None:
        """Test completing a workflow."""
        spec = WorkflowSpec(
            name="test-workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent="agent-1")],
        )
        workflow = Workflow(spec=spec)
        workflow.start()
        workflow.complete(results={"output": "success"})

        assert workflow.status.phase == EntityStatus.SUCCEEDED
        assert workflow.status.progress == 100.0
        assert workflow.status.results["output"] == "success"
        assert workflow.status.completed_at is not None

    def test_fail_workflow(self) -> None:
        """Test failing a workflow."""
        spec = WorkflowSpec(
            name="test-workflow",
            steps=[WorkflowStep(id="s1", name="Step 1", agent="agent-1")],
        )
        workflow = Workflow(spec=spec)
        workflow.start()
        workflow.fail("Something went wrong")

        assert workflow.status.phase == EntityStatus.FAILED
        assert workflow.status.error == "Something went wrong"


class TestToolSpec:
    """Tests for ToolSpec model."""

    def test_create_internal_tool(self) -> None:
        """Test creating an internal tool spec."""
        spec = ToolSpec(
            name="read_file",
            description="Read a file from disk",
            parameters={"path": {"type": "string"}},
        )
        assert spec.name == "read_file"
        assert not spec.is_mcp
        assert spec.mcp_server is None

    def test_create_mcp_tool(self) -> None:
        """Test creating an MCP tool spec."""
        spec = ToolSpec(
            name="search_web",
            description="Search the web",
            is_mcp=True,
            mcp_server="http://localhost:3000",
        )
        assert spec.is_mcp
        assert spec.mcp_server == "http://localhost:3000"


class TestTool:
    """Tests for Tool model."""

    def test_create_tool(self) -> None:
        """Test creating a tool."""
        spec = ToolSpec(name="test_tool", description="A test tool")
        tool = Tool(spec=spec)

        assert tool.id.startswith("tool_")
        assert tool.spec == spec
        assert tool.enabled is True
