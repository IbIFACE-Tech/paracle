"""Tests for AI Compliance Engine.

Tests validation of .parac/ file paths against governance structure rules.
"""

from pathlib import Path

import pytest
from paracle_core.governance.ai_compliance import (
    AIAssistantMonitor,
    AIComplianceEngine,
    FileCategory,
)


class TestAIComplianceEngine:
    """Test AIComplianceEngine validation."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create compliance engine."""
        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()
        (parac_dir / "memory").mkdir()
        (parac_dir / "memory" / "data").mkdir()
        (parac_dir / "memory" / "logs").mkdir()
        return AIComplianceEngine(parac_root=parac_dir)

    def test_validate_database_in_wrong_location(self, engine):
        """Test validation fails for database in .parac root."""
        result = engine.validate_file_path(".parac/costs.db")

        assert not result.is_valid
        assert result.category == FileCategory.OPERATIONAL_DATA
        assert "memory/data" in result.error
        assert result.suggested_path == Path(".parac/memory/data/costs.db")
        assert result.auto_fix_available

    def test_validate_database_in_correct_location(self, engine):
        """Test validation passes for database in correct location."""
        result = engine.validate_file_path(".parac/memory/data/costs.db")

        assert result.is_valid
        assert result.category == FileCategory.OPERATIONAL_DATA
        assert result.error is None

    def test_validate_log_in_wrong_location(self, engine):
        """Test validation fails for log file outside logs/."""
        result = engine.validate_file_path(".parac/agent.log")

        assert not result.is_valid
        assert result.category == FileCategory.LOGS
        assert "memory/logs" in result.error
        assert result.suggested_path == Path(".parac/memory/logs/agent.log")

    def test_validate_log_in_correct_location(self, engine):
        """Test validation passes for log in correct location."""
        result = engine.validate_file_path(".parac/memory/logs/agent_actions.log")

        assert result.is_valid
        assert result.category == FileCategory.LOGS

    def test_validate_knowledge_file(self, engine):
        """Test validation for knowledge base files."""
        # Wrong location
        result = engine.validate_file_path(".parac/architecture.md")
        assert not result.is_valid
        assert result.category == FileCategory.KNOWLEDGE

        # Correct location
        result = engine.validate_file_path(".parac/memory/knowledge/architecture.md")
        assert result.is_valid

    def test_validate_decisions_file(self, engine):
        """Test validation for decisions.md."""
        # Wrong location (root)
        result = engine.validate_file_path(".parac/decisions.md")
        assert not result.is_valid
        assert result.category == FileCategory.DECISIONS
        assert result.suggested_path == Path(".parac/roadmap/decisions.md")

        # Correct location
        result = engine.validate_file_path(".parac/roadmap/decisions.md")
        assert result.is_valid

    def test_validate_user_docs_in_parac(self, engine):
        """Test validation fails for user docs in .parac/."""
        result = engine.validate_file_path(".parac/docs/getting-started.md")

        assert not result.is_valid
        assert result.category == FileCategory.USER_DOCS
        # Check for 'docs' at start of path (works with / or \)
        assert str(result.suggested_path).startswith("docs")
        assert ".parac" not in str(result.suggested_path)

    def test_validate_python_code_in_parac(self, engine):
        """Test validation fails for Python code in .parac/."""
        result = engine.validate_file_path(".parac/my_module.py")

        assert not result.is_valid
        assert result.category == FileCategory.SOURCE_CODE
        # Check for 'packages' at start of path (works with / or \)
        assert str(result.suggested_path).startswith("packages")

    def test_validate_unknown_file_type(self, engine):
        """Test unknown file types are allowed by default."""
        result = engine.validate_file_path(".parac/config/custom.yaml")

        # Unknown types pass validation (no rule matched)
        assert result.is_valid

    def test_validate_batch(self, engine):
        """Test batch validation."""
        paths = [
            ".parac/costs.db",  # Wrong
            ".parac/memory/data/metrics.db",  # Correct
            ".parac/app.log",  # Wrong
            ".parac/memory/logs/errors.log",  # Correct
        ]

        results = engine.validate_batch(paths)

        assert len(results) == 4
        assert not results[0].is_valid  # costs.db wrong
        assert results[1].is_valid  # metrics.db correct
        assert not results[2].is_valid  # app.log wrong
        assert results[3].is_valid  # errors.log correct

    def test_get_violations(self, engine):
        """Test getting only violations."""
        paths = [
            ".parac/costs.db",  # Wrong
            ".parac/memory/data/metrics.db",  # Correct
            ".parac/app.log",  # Wrong
        ]

        violations = engine.get_violations(paths)

        assert len(violations) == 2
        assert all(not v.is_valid for v in violations)

    def test_auto_fix_path(self, engine):
        """Test auto-fix suggestions."""
        # Database in wrong location
        suggested = engine.auto_fix_path(".parac/costs.db")
        assert suggested == Path(".parac/memory/data/costs.db")

        # Log in wrong location
        suggested = engine.auto_fix_path(".parac/debug.log")
        assert suggested == Path(".parac/memory/logs/debug.log")

        # Already correct - no fix needed
        suggested = engine.auto_fix_path(".parac/memory/data/costs.db")
        assert suggested is None

    def test_generate_pre_save_validation(self, engine):
        """Test pre-save validation for IDE hooks."""
        # Valid path
        response = engine.generate_pre_save_validation(".parac/memory/data/costs.db")
        assert response["allow_save"] is True

        # Invalid path
        response = engine.generate_pre_save_validation(".parac/costs.db")
        assert response["allow_save"] is False
        assert "error" in response
        assert "suggested_path" in response
        assert response["auto_fix_available"] is True
        assert "quick_fix" in response

    def test_get_structure_documentation(self, engine):
        """Test getting documentation for categories."""
        docs = engine.get_structure_documentation(FileCategory.OPERATIONAL_DATA)
        assert "memory/data" in docs
        assert ".db" in docs

        docs = engine.get_structure_documentation(FileCategory.LOGS)
        assert "memory/logs" in docs
        assert ".log" in docs


class TestAIAssistantMonitor:
    """Test AIAssistantMonitor for real-time monitoring."""

    @pytest.fixture
    def monitor(self, tmp_path):
        """Create assistant monitor."""
        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()
        (parac_dir / "memory").mkdir()
        (parac_dir / "memory" / "data").mkdir()
        (parac_dir / "memory" / "logs").mkdir()
        return AIAssistantMonitor(parac_root=parac_dir)

    def test_on_file_create_allowed(self, monitor):
        """Test file creation allowed for valid path."""
        response = monitor.on_file_create(".parac/memory/data/costs.db")

        assert response["allowed"] is True

    def test_on_file_create_blocked(self, monitor):
        """Test file creation blocked for invalid path."""
        response = monitor.on_file_create(".parac/costs.db")

        assert response["allowed"] is False
        assert "error" in response
        assert "suggested_path" in response
        assert response["auto_fix_available"] is True
        assert "documentation" in response

    def test_violations_log(self, monitor):
        """Test violations are logged."""
        # Create some violations
        monitor.on_file_create(".parac/costs.db")
        monitor.on_file_create(".parac/app.log")

        assert len(monitor.violations_log) == 2

        # Check report generation
        report = monitor.get_violations_report()
        assert "Violation 1" in report
        assert "Violation 2" in report
        assert "costs.db" in report
        assert "app.log" in report

    def test_clear_violations_log(self, monitor):
        """Test clearing violations log."""
        monitor.on_file_create(".parac/costs.db")
        assert len(monitor.violations_log) == 1

        monitor.clear_violations_log()
        assert len(monitor.violations_log) == 0

    def test_on_file_move(self, monitor):
        """Test file move validation."""
        # Move to invalid location
        response = monitor.on_file_move(
            ".parac/memory/data/costs.db", ".parac/costs.db"
        )

        assert response["allowed"] is False

        # Move to valid location
        response = monitor.on_file_move(
            ".parac/costs.db", ".parac/memory/data/costs.db"
        )

        assert response["allowed"] is True


class TestSingletonAccessors:
    """Test singleton accessor functions."""

    def test_get_compliance_engine(self, tmp_path):
        """Test get_compliance_engine returns singleton."""
        from paracle_core.governance.ai_compliance import (
            get_compliance_engine,
        )

        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()

        engine1 = get_compliance_engine(parac_root=parac_dir)
        engine2 = get_compliance_engine()

        # Should return same instance
        assert engine1 is engine2

    def test_get_assistant_monitor(self, tmp_path):
        """Test get_assistant_monitor returns singleton."""
        from paracle_core.governance.ai_compliance import (
            get_assistant_monitor,
        )

        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()

        monitor1 = get_assistant_monitor(parac_root=parac_dir)
        monitor2 = get_assistant_monitor()

        # Should return same instance
        assert monitor1 is monitor2


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create compliance engine."""
        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()
        (parac_dir / "memory").mkdir()
        (parac_dir / "memory" / "data").mkdir()
        (parac_dir / "memory" / "logs").mkdir()
        (parac_dir / "memory" / "knowledge").mkdir()
        return AIComplianceEngine(parac_root=parac_dir)

    def test_copilot_creates_database(self, engine):
        """Simulate Copilot trying to create database in wrong location."""
        # Copilot suggests: .parac/costs.db
        result = engine.validate_file_path(".parac/costs.db")

        # Should fail validation
        assert not result.is_valid
        # Check path ends with correct location (works with / or \)
        expected = ".parac/memory/data/costs.db"
        actual = str(result.suggested_path).replace("\\", "/")
        assert actual == expected

        # Copilot should use suggested path instead
        result = engine.validate_file_path(result.suggested_path)
        assert result.is_valid

    def test_multiple_file_creation(self, engine):
        """Simulate creating multiple files at once."""
        proposed_paths = [
            ".parac/costs.db",
            ".parac/logs/app.log",
            ".parac/architecture.md",
            ".parac/config.yaml",
        ]

        violations = engine.get_violations(proposed_paths)

        # Should have 3 violations (all but config.yaml)
        assert len(violations) == 3

        # Get corrected paths
        corrected_paths = [
            result.suggested_path if not result.is_valid else result.path
            for result in engine.validate_batch(proposed_paths)
        ]

        # Validate all corrected paths pass or are unknown types
        for path in corrected_paths:
            engine.validate_file_path(path)
            # Unknown types (config.yaml) stay in original location

    def test_real_time_blocking(self, engine):
        """Simulate real-time validation during file creation."""
        # IDE calls validation before saving
        validation = engine.generate_pre_save_validation(".parac/costs.db")

        # Should block save
        assert validation["allow_save"] is False
        assert "quick_fix" in validation

        # Apply quick fix
        correct_path = validation["suggested_path"]

        # Validate again with correct path
        validation = engine.generate_pre_save_validation(correct_path)
        assert validation["allow_save"] is True
