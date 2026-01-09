"""Tests for the governance logging module.

Tests cover:
- GovernanceLogger functionality
- Agent context management
- Session context management
- Action and decision logging
- Log file writing
"""

import tempfile
from pathlib import Path

import pytest
from paracle_core.governance import (
    AgentContext,
    GovernanceActionType,
    GovernanceAgentType,
    GovernanceLogger,
    SessionContext,
    agent_context,
    log_action,
    log_decision,
    session_context,
)
from paracle_core.governance.context import get_current_agent, get_current_session


class TestGovernanceActionType:
    """Tests for GovernanceActionType enum."""

    def test_all_action_types_exist(self):
        """Test that all expected action types are defined."""
        expected = [
            "IMPLEMENTATION",
            "TEST",
            "REVIEW",
            "DOCUMENTATION",
            "REFACTORING",
            "BUGFIX",
            "DECISION",
            "PLANNING",
            "UPDATE",
            "SESSION",
            "SYNC",
            "VALIDATION",
            "INIT",
        ]
        for action in expected:
            assert hasattr(GovernanceActionType, action)
            assert GovernanceActionType[action].value == action


class TestGovernanceAgentType:
    """Tests for GovernanceAgentType enum."""

    def test_all_agent_types_exist(self):
        """Test that all expected agent types are defined."""
        expected = {
            "PM": "PMAgent",
            "ARCHITECT": "ArchitectAgent",
            "CODER": "CoderAgent",
            "TESTER": "TesterAgent",
            "REVIEWER": "ReviewerAgent",
            "DOCUMENTER": "DocumenterAgent",
            "SYSTEM": "SystemAgent",
        }
        for key, value in expected.items():
            assert hasattr(GovernanceAgentType, key)
            assert GovernanceAgentType[key].value == value

    def test_from_string_exact_match(self):
        """Test parsing agent type from exact string."""
        assert (
            GovernanceAgentType.from_string("CoderAgent") == GovernanceAgentType.CODER
        )
        assert (
            GovernanceAgentType.from_string("TesterAgent") == GovernanceAgentType.TESTER
        )

    def test_from_string_lowercase(self):
        """Test parsing agent type from lowercase."""
        assert GovernanceAgentType.from_string("coder") == GovernanceAgentType.CODER
        assert GovernanceAgentType.from_string("tester") == GovernanceAgentType.TESTER

    def test_from_string_uppercase(self):
        """Test parsing agent type from uppercase."""
        assert GovernanceAgentType.from_string("CODER") == GovernanceAgentType.CODER

    def test_from_string_unknown(self):
        """Test parsing unknown agent defaults to SYSTEM."""
        assert GovernanceAgentType.from_string("unknown") == GovernanceAgentType.SYSTEM
        assert GovernanceAgentType.from_string("foo") == GovernanceAgentType.SYSTEM


class TestAgentContext:
    """Tests for AgentContext."""

    def test_agent_context_sets_current_agent(self):
        """Test that agent context sets the current agent."""
        with AgentContext(GovernanceAgentType.CODER):
            assert get_current_agent() == GovernanceAgentType.CODER

    def test_agent_context_restores_on_exit(self):
        """Test that agent context restores previous agent on exit."""
        original = get_current_agent()
        with AgentContext(GovernanceAgentType.TESTER):
            assert get_current_agent() == GovernanceAgentType.TESTER
        assert get_current_agent() == original

    def test_agent_context_from_string(self):
        """Test agent context from string."""
        with AgentContext("CoderAgent"):
            assert get_current_agent() == GovernanceAgentType.CODER

    def test_nested_agent_contexts(self):
        """Test nested agent contexts."""
        with AgentContext(GovernanceAgentType.ARCHITECT):
            assert get_current_agent() == GovernanceAgentType.ARCHITECT
            with AgentContext(GovernanceAgentType.CODER):
                assert get_current_agent() == GovernanceAgentType.CODER
            assert get_current_agent() == GovernanceAgentType.ARCHITECT


class TestSessionContext:
    """Tests for SessionContext."""

    def test_session_context_sets_session_id(self):
        """Test that session context sets a session ID."""
        with SessionContext("Test session") as ctx:
            assert get_current_session() is not None
            assert get_current_session() == ctx.session_id

    def test_session_context_clears_on_exit(self):
        """Test that session ID is cleared on exit."""
        with SessionContext("Test"):
            assert get_current_session() is not None
        assert get_current_session() is None

    def test_session_context_with_agent(self):
        """Test session context with agent."""
        with SessionContext("Test", agent=GovernanceAgentType.CODER):
            assert get_current_agent() == GovernanceAgentType.CODER
            assert get_current_session() is not None

    def test_session_duration(self):
        """Test session duration tracking."""
        with SessionContext("Test") as ctx:
            import time

            time.sleep(0.01)
            duration = ctx.duration_seconds
            assert duration is not None
            assert duration > 0


class TestGovernanceLogger:
    """Tests for GovernanceLogger."""

    @pytest.fixture
    def temp_parac(self):
        """Create temporary .parac directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parac_dir = Path(tmpdir) / ".parac"
            parac_dir.mkdir()
            logs_dir = parac_dir / "memory" / "logs"
            logs_dir.mkdir(parents=True)
            yield parac_dir

    def test_logger_initialization(self, temp_parac):
        """Test logger initializes correctly."""
        logger = GovernanceLogger(temp_parac)
        assert logger.parac_root == temp_parac
        assert logger.logs_dir.exists()

    def test_log_action(self, temp_parac):
        """Test logging an action."""
        logger = GovernanceLogger(temp_parac)
        entry = logger.log(
            GovernanceActionType.IMPLEMENTATION,
            "Test action",
            agent=GovernanceAgentType.CODER,
        )

        assert entry.action == GovernanceActionType.IMPLEMENTATION
        assert entry.agent == GovernanceAgentType.CODER
        assert entry.description == "Test action"

        # Check file was written
        content = logger.actions_log.read_text()
        assert "Test action" in content
        assert "[CoderAgent]" in content
        assert "[IMPLEMENTATION]" in content

    def test_log_action_with_context(self, temp_parac):
        """Test logging uses agent context."""
        logger = GovernanceLogger(temp_parac)

        with AgentContext(GovernanceAgentType.TESTER):
            entry = logger.log(GovernanceActionType.TEST, "Test with context")

        assert entry.agent == GovernanceAgentType.TESTER

    def test_log_action_string_action(self, temp_parac):
        """Test logging with string action type."""
        logger = GovernanceLogger(temp_parac)
        entry = logger.log("BUGFIX", "Fixed bug")
        assert entry.action == GovernanceActionType.BUGFIX

    def test_log_decision(self, temp_parac):
        """Test logging a decision."""
        logger = GovernanceLogger(temp_parac)
        entry = logger.log_decision(
            decision="Use PostgreSQL",
            rationale="Better scalability",
            impact="Requires Docker",
            agent=GovernanceAgentType.ARCHITECT,
        )

        assert entry.decision == "Use PostgreSQL"
        assert entry.rationale == "Better scalability"
        assert entry.impact == "Requires Docker"

        # Check decisions log was written
        content = logger.decisions_log.read_text()
        assert "Use PostgreSQL" in content
        assert "Better scalability" in content

        # Check action log also has the decision
        actions_content = logger.actions_log.read_text()
        assert "[DECISION]" in actions_content

    def test_get_recent_actions(self, temp_parac):
        """Test getting recent actions."""
        logger = GovernanceLogger(temp_parac)

        for i in range(5):
            logger.log(GovernanceActionType.IMPLEMENTATION, f"Action {i}")

        recent = logger.get_recent_actions(3)
        assert len(recent) == 3
        assert "Action 4" in recent[-1]

    def test_get_agent_actions(self, temp_parac):
        """Test getting actions by agent."""
        logger = GovernanceLogger(temp_parac)

        logger.log(
            GovernanceActionType.IMPLEMENTATION,
            "Coder action",
            agent=GovernanceAgentType.CODER,
        )
        logger.log(
            GovernanceActionType.TEST, "Tester action", agent=GovernanceAgentType.TESTER
        )
        logger.log(
            GovernanceActionType.IMPLEMENTATION,
            "Another coder",
            agent=GovernanceAgentType.CODER,
        )

        coder_actions = logger.get_agent_actions(GovernanceAgentType.CODER)
        assert len(coder_actions) == 2
        for action in coder_actions:
            assert "[CoderAgent]" in action


class TestConvenienceFunctions:
    """Tests for log_action and log_decision convenience functions."""

    @pytest.fixture
    def temp_parac_with_logger(self):
        """Create temp .parac and set up logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parac_dir = Path(tmpdir) / ".parac"
            parac_dir.mkdir()
            logs_dir = parac_dir / "memory" / "logs"
            logs_dir.mkdir(parents=True)

            # Reset the global logger and create new one
            import paracle_core.governance.logger as logger_module

            logger_module._governance_logger = GovernanceLogger(parac_dir)
            yield parac_dir
            logger_module._governance_logger = None

    def test_log_action_function(self, temp_parac_with_logger):
        """Test log_action convenience function."""
        entry = log_action(
            GovernanceActionType.IMPLEMENTATION,
            "Convenience function test",
            agent=GovernanceAgentType.CODER,
        )

        assert entry is not None
        assert entry.description == "Convenience function test"

    def test_log_action_with_string_types(self, temp_parac_with_logger):
        """Test log_action with string types."""
        entry = log_action("BUGFIX", "String type test", agent="CoderAgent")
        assert entry is not None
        assert entry.action == GovernanceActionType.BUGFIX

    def test_log_decision_function(self, temp_parac_with_logger):
        """Test log_decision convenience function."""
        entry = log_decision(
            decision="Test decision",
            rationale="Test rationale",
            impact="Test impact",
        )

        assert entry is not None
        assert entry.decision == "Test decision"


class TestAgentContextFunction:
    """Tests for agent_context context manager function."""

    def test_agent_context_function(self):
        """Test agent_context function."""
        with agent_context("CoderAgent") as ctx:
            assert ctx.agent == GovernanceAgentType.CODER
            assert get_current_agent() == GovernanceAgentType.CODER


class TestSessionContextFunction:
    """Tests for session_context context manager function."""

    def test_session_context_function(self):
        """Test session_context function."""
        with session_context("Test session") as ctx:
            assert ctx.description == "Test session"
            assert get_current_session() is not None

    def test_session_context_with_agent(self):
        """Test session_context with agent."""
        with session_context("Test", agent="TesterAgent") as ctx:
            assert get_current_agent() == GovernanceAgentType.TESTER
