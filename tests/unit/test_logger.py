"""Unit tests for paracle_core.parac.logger."""

from datetime import datetime
from pathlib import Path

import pytest

from paracle_core.parac.logger import (
    ActionType,
    AgentLogger,
    AgentType,
    DecisionEntry,
    LogEntry,
    get_logger,
    log_action,
)


class TestAgentLogger:
    """Tests for AgentLogger class."""

    @pytest.fixture
    def temp_parac(self, tmp_path: Path) -> Path:
        """Create a temporary .parac/ structure."""
        parac_dir = tmp_path / ".parac"
        (parac_dir / "memory" / "logs").mkdir(parents=True)
        return parac_dir

    @pytest.fixture
    def logger(self, temp_parac: Path) -> AgentLogger:
        """Create a logger for testing."""
        return AgentLogger(temp_parac)

    def test_logger_creates_logs_directory(self, tmp_path: Path) -> None:
        """Test that logger creates logs directory if missing."""
        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()
        # logs directory doesn't exist yet

        logger = AgentLogger(parac_dir)

        assert logger.logs_dir.exists()
        assert logger.logs_dir == parac_dir / "memory" / "logs"

    def test_log_creates_entry(self, logger: AgentLogger) -> None:
        """Test that log() creates an entry."""
        entry = logger.log(
            agent=AgentType.SYSTEM,
            action=ActionType.SYNC,
            description="Test sync action",
        )

        assert isinstance(entry, LogEntry)
        assert entry.agent == AgentType.SYSTEM
        assert entry.action == ActionType.SYNC
        assert entry.description == "Test sync action"
        assert entry.timestamp is not None

    def test_log_writes_to_file(self, logger: AgentLogger) -> None:
        """Test that log() writes to the actions log file."""
        logger.log(
            agent=AgentType.CODER,
            action=ActionType.IMPLEMENTATION,
            description="Added new feature",
        )

        assert logger.actions_log.exists()
        content = logger.actions_log.read_text()
        assert "[CoderAgent]" in content
        assert "[IMPLEMENTATION]" in content
        assert "Added new feature" in content

    def test_log_with_details(self, logger: AgentLogger) -> None:
        """Test that log() stores details."""
        entry = logger.log(
            agent=AgentType.TESTER,
            action=ActionType.TEST,
            description="Ran unit tests",
            details={"passed": 10, "failed": 0},
        )

        assert entry.details == {"passed": 10, "failed": 0}

    def test_log_decision_creates_entry(self, logger: AgentLogger) -> None:
        """Test that log_decision() creates a decision entry."""
        entry = logger.log_decision(
            agent=AgentType.ARCHITECT,
            decision="Use hexagonal architecture",
            rationale="Better separation of concerns",
            impact="High - affects all packages",
        )

        assert isinstance(entry, DecisionEntry)
        assert entry.agent == AgentType.ARCHITECT
        assert entry.decision == "Use hexagonal architecture"
        assert entry.rationale == "Better separation of concerns"
        assert entry.impact == "High - affects all packages"

    def test_log_decision_writes_to_both_files(self, logger: AgentLogger) -> None:
        """Test that log_decision() writes to both log files."""
        logger.log_decision(
            agent=AgentType.ARCHITECT,
            decision="Use Pydantic for validation",
            rationale="Type safety",
            impact="Medium",
        )

        # Check decisions log
        assert logger.decisions_log.exists()
        decisions_content = logger.decisions_log.read_text()
        assert "Use Pydantic for validation" in decisions_content
        assert "Type safety" in decisions_content

        # Check actions log (should also have the decision)
        actions_content = logger.actions_log.read_text()
        assert "[DECISION]" in actions_content
        assert "Use Pydantic for validation" in actions_content

    def test_get_recent_actions(self, logger: AgentLogger) -> None:
        """Test that get_recent_actions() returns recent entries."""
        # Log multiple actions
        for i in range(5):
            logger.log(
                agent=AgentType.SYSTEM,
                action=ActionType.UPDATE,
                description=f"Action {i}",
            )

        recent = logger.get_recent_actions(count=3)

        assert len(recent) == 3
        assert "Action 2" in recent[0]
        assert "Action 3" in recent[1]
        assert "Action 4" in recent[2]

    def test_get_recent_actions_empty_file(self, logger: AgentLogger) -> None:
        """Test get_recent_actions() when no actions logged."""
        recent = logger.get_recent_actions()

        assert recent == []

    def test_get_agent_actions(self, logger: AgentLogger) -> None:
        """Test that get_agent_actions() filters by agent."""
        logger.log(AgentType.CODER, ActionType.IMPLEMENTATION, "Code 1")
        logger.log(AgentType.TESTER, ActionType.TEST, "Test 1")
        logger.log(AgentType.CODER, ActionType.BUGFIX, "Code 2")
        logger.log(AgentType.REVIEWER, ActionType.REVIEW, "Review 1")

        coder_actions = logger.get_agent_actions(AgentType.CODER)

        assert len(coder_actions) == 2
        assert all("[CoderAgent]" in line for line in coder_actions)

    def test_get_today_actions(self, logger: AgentLogger) -> None:
        """Test that get_today_actions() filters by today's date."""
        logger.log(AgentType.SYSTEM, ActionType.SYNC, "Today's action")

        today_actions = logger.get_today_actions()

        # Should include the action we just logged
        assert len(today_actions) >= 1
        assert any("Today's action" in line for line in today_actions)


class TestLogActionHelper:
    """Tests for log_action() convenience function."""

    @pytest.fixture
    def temp_parac(self, tmp_path: Path, monkeypatch) -> Path:
        """Create a temporary .parac/ structure and change to it."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        parac_dir = project_dir / ".parac"
        (parac_dir / "memory" / "logs").mkdir(parents=True)

        # Change working directory to the project
        monkeypatch.chdir(project_dir)

        # Reset the global logger
        import paracle_core.parac.logger as logger_module

        logger_module._logger = None

        return parac_dir

    def test_log_action_works(self, temp_parac: Path) -> None:
        """Test that log_action() convenience function works."""
        entry = log_action(ActionType.SYNC, "Test action")

        assert entry is not None
        assert entry.action == ActionType.SYNC
        assert entry.agent == AgentType.SYSTEM  # Default agent

    def test_log_action_with_custom_agent(self, temp_parac: Path) -> None:
        """Test log_action() with a custom agent."""
        entry = log_action(
            ActionType.IMPLEMENTATION,
            "Implemented feature",
            agent=AgentType.CODER,
        )

        assert entry is not None
        assert entry.agent == AgentType.CODER

    def test_log_action_returns_none_when_no_parac(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test that log_action() returns None when no .parac/ found."""
        # Change to a directory without .parac/
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)

        # Reset the global logger
        import paracle_core.parac.logger as logger_module

        logger_module._logger = None

        result = log_action(ActionType.SYNC, "This should silently fail")

        assert result is None  # Should not raise, just return None


class TestActionTypes:
    """Tests for ActionType enum."""

    def test_all_action_types_exist(self) -> None:
        """Test that all expected action types are defined."""
        expected_types = [
            "IMPLEMENTATION",
            "TEST",
            "REVIEW",
            "DOCUMENTATION",
            "DECISION",
            "PLANNING",
            "REFACTORING",
            "BUGFIX",
            "UPDATE",
            "SESSION",
            "SYNC",
            "VALIDATION",
            "INIT",
        ]

        for action_type in expected_types:
            assert hasattr(ActionType, action_type)


class TestAgentTypes:
    """Tests for AgentType enum."""

    def test_all_agent_types_exist(self) -> None:
        """Test that all expected agent types are defined."""
        expected_agents = [
            "PM",
            "ARCHITECT",
            "CODER",
            "TESTER",
            "REVIEWER",
            "DOCUMENTER",
            "SYSTEM",
        ]

        for agent_type in expected_agents:
            assert hasattr(AgentType, agent_type)

    def test_agent_type_values(self) -> None:
        """Test that agent types have correct string values."""
        assert AgentType.PM.value == "PMAgent"
        assert AgentType.ARCHITECT.value == "ArchitectAgent"
        assert AgentType.CODER.value == "CoderAgent"
        assert AgentType.SYSTEM.value == "SystemAgent"
