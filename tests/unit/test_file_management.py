"""Unit tests for multi-file management system.

Tests for:
- FileManagementConfig loading and defaults
- ADRManager CRUD operations
- RoadmapManager operations
- AgentLogger with configurable paths
"""

import tempfile
from datetime import date
from pathlib import Path

import pytest
import yaml


# =============================================================================
# FileManagementConfig Tests
# =============================================================================


class TestFileManagementConfig:
    """Tests for FileManagementConfig Pydantic models."""

    def test_get_defaults(self):
        """Test default configuration."""
        from paracle_core.parac.file_config import FileManagementConfig

        config = FileManagementConfig.get_defaults()

        assert config.logs.base_path == "memory/logs"
        assert config.logs.predefined.actions.enabled is True
        assert config.logs.predefined.security.enabled is False
        assert config.adr.base_path == "roadmap/adr"
        assert config.adr.format == "markdown"
        assert config.roadmap.primary == "roadmap.yaml"

    def test_from_project_yaml(self, tmp_path):
        """Test loading from project.yaml."""
        from paracle_core.parac.file_config import FileManagementConfig

        # Create minimal project.yaml
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text(
            yaml.dump(
                {
                    "name": "test-project",
                    "file_management": {
                        "logs": {
                            "base_path": "custom/logs",
                            "predefined": {
                                "actions": {"enabled": True, "path": "actions.log"},
                                "decisions": {"enabled": True, "path": "decisions.log"},
                                "security": {"enabled": True, "path": "sec.log"},
                                "performance": {"enabled": False, "path": "perf.log"},
                                "risk": {"enabled": False, "path": "risk.log"},
                            },
                        },
                        "adr": {
                            "base_path": "decisions/adr",
                            "enabled": True,
                        },
                        "roadmap": {
                            "base_path": "roadmap",
                            "primary": "main.yaml",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

        config = FileManagementConfig.from_project_yaml(tmp_path)

        assert config.logs.base_path == "custom/logs"
        assert config.logs.predefined.security.enabled is True
        assert config.adr.base_path == "decisions/adr"
        assert config.roadmap.primary == "main.yaml"

    def test_get_enabled_logs(self, tmp_path):
        """Test getting enabled log paths."""
        from paracle_core.parac.file_config import FileManagementConfig

        config = FileManagementConfig.get_defaults()
        enabled_logs = config.get_enabled_logs(tmp_path)

        # Actions and decisions should be enabled by default
        assert "actions" in enabled_logs
        assert "decisions" in enabled_logs

        # Security should be disabled by default
        assert "security" not in enabled_logs

    def test_custom_log_files(self, tmp_path):
        """Test custom log file configuration."""
        from paracle_core.parac.file_config import (
            CustomLogConfig,
            FileManagementConfig,
            LogsConfig,
            PredefinedLogsConfig,
        )

        # Create config with custom log
        config = FileManagementConfig.get_defaults()

        # Add custom log
        custom_log = CustomLogConfig(
            name="my_custom",
            path="custom/my_log.log",
            format="[{timestamp}] {message}",
        )
        config.logs.custom.append(custom_log)

        enabled_logs = config.get_enabled_logs(tmp_path)

        assert "my_custom" in enabled_logs
        assert enabled_logs["my_custom"] == tmp_path / "memory/logs/custom/my_log.log"


# =============================================================================
# ADRManager Tests
# =============================================================================


class TestADRManager:
    """Tests for ADRManager."""

    @pytest.fixture
    def adr_manager(self, tmp_path):
        """Create ADRManager with temp directory."""
        from paracle_core.parac.adr_manager import ADRManager
        from paracle_core.parac.file_config import ADRConfig

        config = ADRConfig(
            base_path="adr",
            enabled=True,
            format="markdown",
            index_file="index.md",
            template="""# {id}: {title}

**Date**: {date}
**Status**: {status}
**Deciders**: {deciders}

## Context

{context}

## Decision

{decision}

## Consequences

{consequences}

## Implementation

{implementation}

## Related Decisions

{related}
""",
            auto_number=True,
            number_format="ADR-{:03d}",
            legacy_file=None,
            migrate_on_init=False,
        )

        return ADRManager(tmp_path, config=config)

    def test_create_adr(self, adr_manager):
        """Test creating a new ADR."""
        adr_id = adr_manager.create(
            title="Use PostgreSQL for persistence",
            context="Need a robust database",
            decision="Use PostgreSQL",
            consequences="Better ACID compliance",
        )

        assert adr_id == "ADR-001"

        # Check file exists
        adr_file = adr_manager.adr_dir / "ADR-001.md"
        assert adr_file.exists()

        # Check content
        content = adr_file.read_text(encoding="utf-8")
        assert "Use PostgreSQL for persistence" in content
        assert "Need a robust database" in content

    def test_create_multiple_adrs(self, adr_manager):
        """Test auto-numbering for multiple ADRs."""
        id1 = adr_manager.create(
            title="First decision",
            context="ctx1",
            decision="dec1",
            consequences="con1",
        )
        id2 = adr_manager.create(
            title="Second decision",
            context="ctx2",
            decision="dec2",
            consequences="con2",
        )

        assert id1 == "ADR-001"
        assert id2 == "ADR-002"

    def test_get_adr(self, adr_manager):
        """Test retrieving an ADR."""
        adr_manager.create(
            title="Test ADR",
            context="Test context",
            decision="Test decision",
            consequences="Test consequences",
        )

        adr = adr_manager.get("ADR-001")

        assert adr is not None
        assert adr.id == "ADR-001"
        assert adr.title == "Test ADR"
        assert adr.context == "Test context"

    def test_get_nonexistent_adr(self, adr_manager):
        """Test getting a nonexistent ADR."""
        adr = adr_manager.get("ADR-999")
        assert adr is None

    def test_list_adrs(self, adr_manager):
        """Test listing ADRs."""
        adr_manager.create(
            title="First",
            context="ctx",
            decision="dec",
            consequences="con",
            status="Accepted",
        )
        adr_manager.create(
            title="Second",
            context="ctx",
            decision="dec",
            consequences="con",
            status="Proposed",
        )

        all_adrs = adr_manager.list()
        assert len(all_adrs) == 2

        # Filter by status
        accepted = adr_manager.list(status="Accepted")
        assert len(accepted) == 1
        assert accepted[0].status == "Accepted"

    def test_update_status(self, adr_manager):
        """Test updating ADR status."""
        adr_manager.create(
            title="Test",
            context="ctx",
            decision="dec",
            consequences="con",
            status="Proposed",
        )

        result = adr_manager.update_status("ADR-001", "Accepted")
        assert result is True

        adr = adr_manager.get("ADR-001")
        assert adr.status == "Accepted"

    def test_search_adrs(self, adr_manager):
        """Test searching ADRs."""
        adr_manager.create(
            title="Database Selection",
            context="Need to choose database",
            decision="Use PostgreSQL",
            consequences="Good ACID support",
        )
        adr_manager.create(
            title="API Design",
            context="Need REST API",
            decision="Use FastAPI",
            consequences="Fast development",
        )

        results = adr_manager.search("database")
        assert len(results) == 1
        assert results[0].title == "Database Selection"

    def test_index_file_updated(self, adr_manager):
        """Test index file is updated on ADR creation."""
        adr_manager.create(
            title="Test ADR",
            context="ctx",
            decision="dec",
            consequences="con",
        )

        index_file = adr_manager.adr_dir / "index.md"
        assert index_file.exists()

        content = index_file.read_text(encoding="utf-8")
        assert "ADR-001" in content
        assert "Test ADR" in content

    def test_count_by_status(self, adr_manager):
        """Test counting ADRs by status."""
        adr_manager.create(
            title="A1",
            context="c",
            decision="d",
            consequences="c",
            status="Accepted",
        )
        adr_manager.create(
            title="A2",
            context="c",
            decision="d",
            consequences="c",
            status="Accepted",
        )
        adr_manager.create(
            title="A3",
            context="c",
            decision="d",
            consequences="c",
            status="Proposed",
        )

        counts = adr_manager.count_by_status()
        assert counts.get("Accepted", 0) == 2
        assert counts.get("Proposed", 0) == 1


# =============================================================================
# RoadmapManager Tests
# =============================================================================


class TestRoadmapManager:
    """Tests for RoadmapManager."""

    @pytest.fixture
    def roadmap_manager(self, tmp_path):
        """Create RoadmapManager with temp directory."""
        from paracle_core.parac.file_config import RoadmapConfig
        from paracle_core.parac.roadmap_manager import RoadmapManager

        config = RoadmapConfig(
            base_path="roadmap",
            primary="roadmap.yaml",
            additional=[],
            sync={"enabled": True, "validate_on_sync": True, "auto_update_state": True},
        )

        # Create primary roadmap
        roadmap_dir = tmp_path / "roadmap"
        roadmap_dir.mkdir(parents=True)

        roadmap_file = roadmap_dir / "roadmap.yaml"
        roadmap_file.write_text(
            yaml.dump(
                {
                    "version": "1.0",
                    "project": "test-project",
                    "phases": [
                        {
                            "id": "phase_1",
                            "name": "Phase 1",
                            "status": "completed",
                            "progress": 100.0,
                        },
                        {
                            "id": "phase_2",
                            "name": "Phase 2",
                            "status": "in_progress",
                            "progress": 50.0,
                        },
                        {
                            "id": "phase_3",
                            "name": "Phase 3",
                            "status": "pending",
                            "progress": 0.0,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        return RoadmapManager(tmp_path, config=config)

    def test_list_roadmaps(self, roadmap_manager):
        """Test listing roadmaps."""
        roadmaps = roadmap_manager.list_roadmaps()

        assert len(roadmaps) == 1
        assert roadmaps[0].name == "primary"
        assert roadmaps[0].exists is True
        assert roadmaps[0].phase_count == 3

    def test_get_roadmap(self, roadmap_manager):
        """Test getting a roadmap."""
        roadmap = roadmap_manager.get_roadmap("primary")

        assert roadmap is not None
        assert roadmap.name == "primary"
        assert len(roadmap.phases) == 3
        assert roadmap.phases[0].id == "phase_1"
        assert roadmap.phases[1].status == "in_progress"

    def test_get_current_phase(self, roadmap_manager):
        """Test getting current phase."""
        current = roadmap_manager.get_current_phase("primary")

        assert current is not None
        assert current.id == "phase_2"
        assert current.status == "in_progress"
        assert current.progress == 50.0

    def test_get_next_phase(self, roadmap_manager):
        """Test getting next pending phase."""
        next_phase = roadmap_manager.get_next_phase("primary")

        assert next_phase is not None
        assert next_phase.id == "phase_3"
        assert next_phase.status == "pending"

    def test_validate_roadmap(self, roadmap_manager):
        """Test validating a roadmap."""
        results = roadmap_manager.validate("primary")

        assert len(results) == 1
        assert results[0].is_valid is True
        assert len(results[0].errors) == 0

    def test_validate_invalid_roadmap(self, tmp_path):
        """Test validating an invalid roadmap."""
        from paracle_core.parac.file_config import RoadmapConfig
        from paracle_core.parac.roadmap_manager import RoadmapManager

        config = RoadmapConfig(
            base_path="roadmap",
            primary="roadmap.yaml",
            additional=[],
        )

        # Create invalid roadmap (duplicate phase IDs)
        roadmap_dir = tmp_path / "roadmap"
        roadmap_dir.mkdir(parents=True)

        roadmap_file = roadmap_dir / "roadmap.yaml"
        roadmap_file.write_text(
            yaml.dump(
                {
                    "version": "1.0",
                    "phases": [
                        {"id": "phase_1", "name": "Phase 1"},
                        {"id": "phase_1", "name": "Duplicate"},  # Duplicate ID
                    ],
                }
            ),
            encoding="utf-8",
        )

        manager = RoadmapManager(tmp_path, config=config)
        results = manager.validate("primary")

        assert len(results) == 1
        assert results[0].is_valid is False
        assert any("Duplicate" in e for e in results[0].errors)

    def test_add_roadmap(self, roadmap_manager):
        """Test adding a new roadmap."""
        result = roadmap_manager.add_roadmap(
            name="tech-debt",
            path="tech-debt.yaml",
            description="Technical debt tracking",
            create_file=True,
        )

        assert result is True

        # Check roadmap was added
        roadmaps = roadmap_manager.list_roadmaps()
        names = [r.name for r in roadmaps]
        assert "tech-debt" in names

        # Check file was created
        tech_debt_file = roadmap_manager.roadmap_dir / "tech-debt.yaml"
        assert tech_debt_file.exists()

    def test_cannot_add_primary(self, roadmap_manager):
        """Test that 'primary' name is reserved."""
        result = roadmap_manager.add_roadmap(
            name="primary",
            path="other.yaml",
        )

        assert result is False

    def test_update_phase_status(self, roadmap_manager):
        """Test updating a phase's status."""
        result = roadmap_manager.update_phase_status("primary", "phase_2", "completed")

        assert result is True

        # Verify change
        roadmap = roadmap_manager.get_roadmap("primary")
        phase_2 = next(p for p in roadmap.phases if p.id == "phase_2")
        assert phase_2.status == "completed"

    def test_update_phase_progress(self, roadmap_manager):
        """Test updating a phase's progress."""
        result = roadmap_manager.update_phase_progress("primary", "phase_2", 75.0)

        assert result is True

        # Verify change
        roadmap = roadmap_manager.get_roadmap("primary")
        phase_2 = next(p for p in roadmap.phases if p.id == "phase_2")
        assert phase_2.progress == 75.0

    def test_get_stats(self, roadmap_manager):
        """Test getting roadmap statistics."""
        stats = roadmap_manager.get_stats()

        assert stats["total_roadmaps"] == 1
        assert stats["total_phases"] == 3
        assert "completed" in stats["phases_by_status"]
        assert "in_progress" in stats["phases_by_status"]
        assert "pending" in stats["phases_by_status"]

    def test_search_phases(self, roadmap_manager):
        """Test searching phases."""
        results = roadmap_manager.search_phases("Phase 2")

        assert len(results) == 1
        roadmap_name, phase = results[0]
        assert roadmap_name == "primary"
        assert phase.id == "phase_2"


# =============================================================================
# AgentLogger Tests (with configurable paths)
# =============================================================================


class TestAgentLoggerConfigurable:
    """Tests for AgentLogger with configurable paths."""

    @pytest.fixture
    def logger_with_config(self, tmp_path):
        """Create AgentLogger with custom config."""
        from paracle_core.parac.file_config import FileManagementConfig
        from paracle_core.parac.logger import AgentLogger

        # Create project.yaml with custom log config
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text(
            yaml.dump(
                {
                    "name": "test-project",
                    "file_management": {
                        "logs": {
                            "base_path": "logs",
                            "predefined": {
                                "actions": {
                                    "enabled": True,
                                    "path": "actions.log",
                                },
                                "decisions": {
                                    "enabled": True,
                                    "path": "decisions.log",
                                },
                                "security": {
                                    "enabled": True,
                                    "path": "security.log",
                                    "format": "structured_json",
                                },
                                "performance": {"enabled": False, "path": "perf.log"},
                                "risk": {"enabled": False, "path": "risk.log"},
                            },
                        },
                        "adr": {"base_path": "adr"},
                        "roadmap": {"base_path": "roadmap", "primary": "roadmap.yaml"},
                    },
                }
            ),
            encoding="utf-8",
        )

        config = FileManagementConfig.from_project_yaml(tmp_path)
        return AgentLogger(tmp_path, config=config)

    def test_log_to_custom_file(self, logger_with_config):
        """Test logging to a custom file."""
        from paracle_core.parac.logger import ActionType, AgentType

        # Log an action
        entry = logger_with_config.log(
            AgentType.CODER,
            ActionType.IMPLEMENTATION,
            "Implemented feature X",
        )

        assert entry is not None
        assert entry.agent == AgentType.CODER

        # Check file was written
        assert logger_with_config.actions_log.exists()

    def test_log_to_security(self, logger_with_config):
        """Test logging to security log."""
        # Security is enabled in our test config
        logger_with_config.log_to("security", "User authenticated", level="INFO")

        # Check file was written
        security_log = logger_with_config.log_files.get("security")
        assert security_log is not None
        assert security_log.exists()

    def test_log_to_disabled_log_raises(self, logger_with_config):
        """Test that logging to disabled log raises error."""
        # Performance is disabled in our test config
        with pytest.raises(ValueError, match="Unknown or disabled log"):
            logger_with_config.log_to("performance", "Test message")

    def test_get_available_logs(self, logger_with_config):
        """Test getting available log names."""
        available = logger_with_config.get_available_logs()

        assert "actions" in available
        assert "decisions" in available
        assert "security" in available
        assert "performance" not in available  # Disabled

    def test_get_log_path(self, logger_with_config):
        """Test getting log file path."""
        path = logger_with_config.get_log_path("actions")
        assert path is not None
        assert path.name == "actions.log"

        path = logger_with_config.get_log_path("nonexistent")
        assert path is None


# =============================================================================
# Integration Tests
# =============================================================================


class TestFileManagementIntegration:
    """Integration tests for the file management system."""

    @pytest.fixture
    def full_setup(self, tmp_path):
        """Create a full .parac setup."""
        from paracle_core.parac.adr_manager import ADRManager
        from paracle_core.parac.file_config import FileManagementConfig
        from paracle_core.parac.logger import AgentLogger
        from paracle_core.parac.roadmap_manager import RoadmapManager

        # Create project.yaml
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text(
            yaml.dump(
                {
                    "name": "integration-test",
                    "file_management": {
                        "logs": {
                            "base_path": "memory/logs",
                            "predefined": {
                                "actions": {"enabled": True, "path": "actions.log"},
                                "decisions": {"enabled": True, "path": "decisions.log"},
                                "security": {"enabled": False, "path": "sec.log"},
                                "performance": {"enabled": False, "path": "perf.log"},
                                "risk": {"enabled": False, "path": "risk.log"},
                            },
                        },
                        "adr": {
                            "base_path": "roadmap/adr",
                            "enabled": True,
                            "template": "# {id}: {title}\n\n{context}\n\n{decision}\n\n{consequences}\n\n{implementation}\n\n{related}",
                        },
                        "roadmap": {
                            "base_path": "roadmap",
                            "primary": "roadmap.yaml",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

        # Create roadmap
        roadmap_dir = tmp_path / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "roadmap.yaml").write_text(
            yaml.dump(
                {
                    "version": "1.0",
                    "phases": [
                        {
                            "id": "phase_1",
                            "name": "Phase 1",
                            "status": "in_progress",
                            "progress": 50.0,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        # Create current_state.yaml for sync
        memory_dir = tmp_path / "memory" / "context"
        memory_dir.mkdir(parents=True)
        (memory_dir / "current_state.yaml").write_text(
            yaml.dump(
                {
                    "current_phase": {
                        "id": "phase_1",
                        "name": "Phase 1",
                        "progress": 50.0,
                    }
                }
            ),
            encoding="utf-8",
        )

        config = FileManagementConfig.from_project_yaml(tmp_path)

        return {
            "parac_root": tmp_path,
            "config": config,
            "logger": AgentLogger(tmp_path, config=config),
            "adr_manager": ADRManager(tmp_path, config=config.adr),
            "roadmap_manager": RoadmapManager(tmp_path, config=config.roadmap),
        }

    def test_full_workflow(self, full_setup):
        """Test a full workflow using all components."""
        from paracle_core.parac.logger import ActionType, AgentType

        logger = full_setup["logger"]
        adr_manager = full_setup["adr_manager"]
        roadmap_manager = full_setup["roadmap_manager"]

        # 1. Log a planning action
        logger.log(AgentType.PM, ActionType.PLANNING, "Started planning session")

        # 2. Create an ADR
        adr_id = adr_manager.create(
            title="Use REST API",
            context="Need API design",
            decision="Use REST",
            consequences="Standard approach",
            status="Proposed",
        )
        assert adr_id == "ADR-001"

        # 3. Log the decision
        logger.log_decision(
            AgentType.ARCHITECT,
            "Use REST API",
            "Industry standard",
            "Easy to maintain",
        )

        # 4. Update ADR status
        adr_manager.update_status(adr_id, "Accepted")

        # 5. Check roadmap
        current_phase = roadmap_manager.get_current_phase()
        assert current_phase is not None
        assert current_phase.id == "phase_1"

        # 6. Validate roadmap
        validation = roadmap_manager.validate()
        assert all(r.is_valid for r in validation)

        # 7. Verify logs exist
        assert logger.actions_log.exists()
        assert logger.decisions_log.exists()
