"""Unit tests for paracle_meta.sessions module."""

import pytest

from paracle_meta.sessions.base import (
    Session,
    SessionConfig,
    SessionMessage,
    SessionStatus,
)
from paracle_meta.sessions.chat import (
    CAPABILITY_TOOLS,
    ChatConfig,
    ChatSession,
    DEFAULT_CHAT_SYSTEM_PROMPT,
)
from paracle_meta.sessions.plan import (
    Plan,
    PlanConfig,
    PlanSession,
    PlanStep,
    StepStatus,
)
from paracle_meta.capabilities.providers.mock import MockProvider
from paracle_meta.registry import CapabilityRegistry


class TestSessionMessage:
    """Tests for SessionMessage."""

    def test_create_message(self):
        """Test creating a message."""
        msg = SessionMessage(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.id.startswith("msg_")
        assert msg.timestamp is not None

    def test_to_dict(self):
        """Test message serialization."""
        msg = SessionMessage(role="assistant", content="Hi!")

        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Hi!"
        assert "timestamp" in data

    def test_from_dict(self):
        """Test message deserialization."""
        data = {
            "role": "user",
            "content": "Test",
            "timestamp": "2024-01-01T00:00:00+00:00",
        }

        msg = SessionMessage.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "Test"


class TestSessionConfig:
    """Tests for SessionConfig."""

    def test_default_values(self):
        """Test default configuration."""
        config = SessionConfig()

        assert config.system_prompt is None
        assert config.max_turns == 100
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.enable_tools is True


class TestSessionStatus:
    """Tests for SessionStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert SessionStatus.CREATED.value == "created"
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.COMPLETED.value == "completed"


class TestChatConfig:
    """Tests for ChatConfig."""

    def test_default_system_prompt(self):
        """Test default system prompt is set."""
        config = ChatConfig()

        assert config.system_prompt == DEFAULT_CHAT_SYSTEM_PROMPT

    def test_default_capabilities(self):
        """Test default enabled capabilities."""
        config = ChatConfig()

        assert "filesystem" in config.enabled_capabilities
        assert "memory" in config.enabled_capabilities

    def test_custom_capabilities(self):
        """Test custom enabled capabilities."""
        config = ChatConfig(enabled_capabilities=["shell", "code_creation"])

        assert "shell" in config.enabled_capabilities
        assert "filesystem" not in config.enabled_capabilities


class TestCapabilityTools:
    """Tests for CAPABILITY_TOOLS definitions."""

    def test_filesystem_tools(self):
        """Test filesystem tools are defined."""
        assert "filesystem" in CAPABILITY_TOOLS

        tools = CAPABILITY_TOOLS["filesystem"]
        tool_names = [t.name for t in tools]

        assert "read_file" in tool_names
        assert "write_file" in tool_names
        assert "list_directory" in tool_names

    def test_memory_tools(self):
        """Test memory tools are defined."""
        assert "memory" in CAPABILITY_TOOLS

        tools = CAPABILITY_TOOLS["memory"]
        tool_names = [t.name for t in tools]

        assert "remember" in tool_names
        assert "recall" in tool_names


class TestChatSession:
    """Tests for ChatSession."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        return MockProvider()

    @pytest.fixture
    def registry(self):
        """Create registry."""
        return CapabilityRegistry()

    @pytest.fixture
    def chat_session(self, mock_provider, registry):
        """Create chat session."""
        return ChatSession(mock_provider, registry)

    @pytest.mark.asyncio
    async def test_initialize(self, chat_session):
        """Test session initialization."""
        await chat_session.initialize()

        assert chat_session.status == SessionStatus.ACTIVE
        assert len(chat_session.tools) > 0

    @pytest.mark.asyncio
    async def test_send_message(self, chat_session, mock_provider):
        """Test sending a message."""
        await mock_provider.initialize()
        await chat_session.initialize()

        response = await chat_session.send("Hello!")

        assert response.role == "assistant"
        assert response.content is not None
        assert chat_session.turn_count == 1

    @pytest.mark.asyncio
    async def test_conversation_history(self, chat_session, mock_provider):
        """Test conversation history tracking."""
        await mock_provider.initialize()
        await chat_session.initialize()

        await chat_session.send("First message")
        await chat_session.send("Second message")

        history = chat_session.get_history()
        assert len(history) >= 4  # 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_session_context_manager(self, mock_provider, registry):
        """Test session as context manager."""
        async with ChatSession(mock_provider, registry) as session:
            assert session.status == SessionStatus.ACTIVE

        assert session.status == SessionStatus.COMPLETED


class TestPlanStep:
    """Tests for PlanStep."""

    def test_create_step(self):
        """Test creating a plan step."""
        step = PlanStep(
            id="step_1",
            description="Analyze requirements",
            action="Review the specification document",
        )

        assert step.id == "step_1"
        assert step.status == StepStatus.PENDING
        assert step.result is None

    def test_to_dict(self):
        """Test step serialization."""
        step = PlanStep(
            id="step_1",
            description="Test step",
            action="Do something",
            capability="filesystem",
        )

        data = step.to_dict()
        assert data["id"] == "step_1"
        assert data["capability"] == "filesystem"

    def test_from_dict(self):
        """Test step deserialization."""
        data = {
            "id": "step_2",
            "description": "Write code",
            "action": "Implement function",
            "status": "completed",
        }

        step = PlanStep.from_dict(data)
        assert step.id == "step_2"
        assert step.status == StepStatus.COMPLETED


class TestPlan:
    """Tests for Plan."""

    def test_create_plan(self):
        """Test creating a plan."""
        steps = [
            PlanStep(id="1", description="Step 1", action="Action 1"),
            PlanStep(id="2", description="Step 2", action="Action 2"),
        ]

        plan = Plan(
            goal="Build a feature",
            summary="Two-step plan",
            steps=steps,
        )

        assert plan.goal == "Build a feature"
        assert len(plan.steps) == 2
        assert plan.progress == 0.0

    def test_completed_steps(self):
        """Test completed steps counting."""
        steps = [
            PlanStep(
                id="1", description="S1", action="A1", status=StepStatus.COMPLETED
            ),
            PlanStep(id="2", description="S2", action="A2", status=StepStatus.PENDING),
        ]

        plan = Plan(goal="Test", summary="Test", steps=steps)

        assert plan.completed_steps == 1
        assert plan.progress == 50.0

    def test_is_complete(self):
        """Test plan completion check."""
        steps = [
            PlanStep(
                id="1", description="S1", action="A1", status=StepStatus.COMPLETED
            ),
            PlanStep(
                id="2", description="S2", action="A2", status=StepStatus.COMPLETED
            ),
        ]

        plan = Plan(goal="Test", summary="Test", steps=steps)

        assert plan.is_complete is True

    def test_get_next_step(self):
        """Test getting next step."""
        steps = [
            PlanStep(
                id="1", description="S1", action="A1", status=StepStatus.COMPLETED
            ),
            PlanStep(id="2", description="S2", action="A2", status=StepStatus.PENDING),
        ]

        plan = Plan(goal="Test", summary="Test", steps=steps)

        next_step = plan.get_next_step()
        assert next_step.id == "2"

    def test_get_next_step_with_dependencies(self):
        """Test getting next step respects dependencies."""
        steps = [
            PlanStep(id="1", description="S1", action="A1", status=StepStatus.PENDING),
            PlanStep(
                id="2",
                description="S2",
                action="A2",
                status=StepStatus.PENDING,
                depends_on=["1"],
            ),
        ]

        plan = Plan(goal="Test", summary="Test", steps=steps)

        # Step 2 depends on step 1, so step 1 should be returned
        next_step = plan.get_next_step()
        assert next_step.id == "1"

    def test_to_dict(self):
        """Test plan serialization."""
        plan = Plan(
            goal="Test goal",
            summary="Test summary",
            steps=[PlanStep(id="1", description="S1", action="A1")],
            risks=["Risk 1"],
        )

        data = plan.to_dict()
        assert data["goal"] == "Test goal"
        assert len(data["steps"]) == 1
        assert data["risks"] == ["Risk 1"]


class TestPlanConfig:
    """Tests for PlanConfig."""

    def test_default_values(self):
        """Test default configuration."""
        config = PlanConfig()

        assert config.auto_execute is False
        assert config.require_approval is True
        assert config.max_retries == 2

    def test_system_prompt_set(self):
        """Test default system prompt is set."""
        config = PlanConfig()

        assert config.system_prompt is not None
        assert "planning" in config.system_prompt.lower()


class TestPlanSession:
    """Tests for PlanSession."""

    @pytest.fixture
    def mock_provider(self):
        """Create mock provider."""
        return MockProvider()

    @pytest.fixture
    def registry(self):
        """Create registry."""
        return CapabilityRegistry()

    @pytest.fixture
    def plan_session(self, mock_provider, registry):
        """Create plan session."""
        return PlanSession(mock_provider, registry)

    @pytest.mark.asyncio
    async def test_initialize(self, plan_session):
        """Test session initialization."""
        await plan_session.initialize()

        assert plan_session.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_create_plan(self, plan_session, mock_provider):
        """Test creating a plan."""
        await mock_provider.initialize()
        await plan_session.initialize()

        plan = await plan_session.create_plan("Build a REST API")

        assert plan is not None
        assert plan.goal == "Build a REST API"
        assert len(plan.steps) > 0

    @pytest.mark.asyncio
    async def test_send_creates_plan(self, plan_session, mock_provider):
        """Test send creates a plan."""
        await mock_provider.initialize()
        await plan_session.initialize()

        response = await plan_session.send("Create user authentication")

        assert response.role == "assistant"
        assert plan_session.current_plan is not None

    @pytest.mark.asyncio
    async def test_list_plans(self, plan_session, mock_provider):
        """Test listing plans."""
        await mock_provider.initialize()
        await plan_session.initialize()

        await plan_session.create_plan("Plan 1")
        await plan_session.create_plan("Plan 2")

        plans = plan_session.list_plans()
        assert len(plans) == 2
