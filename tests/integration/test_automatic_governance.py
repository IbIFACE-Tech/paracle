"""Integration tests for automatic governance system."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml
from paracle_core.governance import (
    async_agent_operation,
    get_state_manager,
    log_agent_action,
    reset_governance_logger,
    reset_state_manager,
)
from paracle_core.governance.logger import GovernanceLogger
from paracle_core.governance.types import GovernanceActionType


@pytest.fixture
def temp_project():
    """Create a complete temporary project structure."""
    # Reset the global singletons before each test
    reset_state_manager()
    reset_governance_logger()
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        parac_dir = project_dir / ".parac"

        # Create directory structure
        (parac_dir / "memory" / "logs").mkdir(parents=True)
        (parac_dir / "memory" / "context").mkdir(parents=True)
        (parac_dir / "roadmap").mkdir(parents=True)

        # Create current_state.yaml
        state_file = parac_dir / "memory" / "context" / "current_state.yaml"
        initial_state = {
            "project": {
                "name": "integration-test",
                "version": "0.1.0",
            },
            "current_phase": {
                "id": "phase_1",
                "name": "Development",
                "status": "in_progress",
                "progress": 0,
                "completed": [],
                "in_progress": ["feature_a", "feature_b"],
            },
            "recent_updates": [],
            "revision": 1,
        }
        state_file.write_text(yaml.dump(initial_state))

        # Create roadmap.yaml
        roadmap_file = parac_dir / "roadmap" / "roadmap.yaml"
        roadmap = {
            "phases": [
                {
                    "id": "phase_1",
                    "name": "Development",
                    "status": "in_progress",
                    "deliverables": [
                        {
                            "id": "feature_a",
                            "name": "Feature A",
                            "status": "in_progress",
                        },
                        {
                            "id": "feature_b",
                            "name": "Feature B",
                            "status": "in_progress",
                        },
                    ],
                }
            ]
        }
        roadmap_file.write_text(yaml.dump(roadmap))

        yield project_dir, parac_dir


class TestEndToEndWorkflow:
    """End-to-end tests simulating real agent workflows."""

    @pytest.mark.asyncio
    async def test_complete_feature_development(self, temp_project, monkeypatch):
        """Test complete feature development workflow with automatic logging."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        # Initialize governance
        logger = GovernanceLogger(parac_root=parac_dir)
        state_manager = get_state_manager(parac_root=parac_dir)

        # Simulate feature implementation
        @log_agent_action("CoderAgent", GovernanceActionType.IMPLEMENTATION)
        async def implement_feature(feature_id: str):
            """Implement a feature."""
            await asyncio.sleep(0.01)  # Simulate work
            return f"{feature_id} implemented"

        # Implement feature A
        result = await implement_feature("feature_a")
        assert result == "feature_a implemented"

        # Mark deliverable complete
        await state_manager.on_deliverable_completed(
            deliverable_id="feature_a",
            agent="CoderAgent",
            phase="phase_1",
            description="Implemented Feature A",
        )

        # Verify logging
        log_file = parac_dir / "memory" / "logs" / "agent_actions.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "CoderAgent" in log_content
        assert "IMPLEMENTATION" in log_content
        assert "Implement Feature" in log_content  # Human-readable format

        # Verify state update
        state_file = parac_dir / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        assert "feature_a" in state["current_phase"]["completed"]
        assert "feature_a" not in state["current_phase"]["in_progress"]
        assert state["current_phase"]["progress"] == 50  # 1 of 2

    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self, temp_project, monkeypatch):
        """Test multiple agents working together with automatic governance."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        state_manager = get_state_manager(parac_root=parac_dir)

        # Agent 1: Architect designs
        @log_agent_action("ArchitectAgent", GovernanceActionType.IMPLEMENTATION)
        async def design_architecture():
            await asyncio.sleep(0.01)
            return "Architecture designed"

        # Agent 2: Coder implements
        @log_agent_action("CoderAgent", GovernanceActionType.IMPLEMENTATION)
        async def implement_code():
            await asyncio.sleep(0.01)
            return "Code implemented"

        # Agent 3: Tester validates
        @log_agent_action("TesterAgent", GovernanceActionType.TEST)
        async def run_tests():
            await asyncio.sleep(0.01)
            return "Tests passed"

        # Execute workflow
        design_result = await design_architecture()
        impl_result = await implement_code()
        test_result = await run_tests()

        assert design_result == "Architecture designed"
        assert impl_result == "Code implemented"
        assert test_result == "Tests passed"

        # Mark both features complete
        await state_manager.on_deliverable_completed(
            deliverable_id="feature_a",
            agent="CoderAgent",
            phase="phase_1",
            description="Feature A implemented",
        )
        await state_manager.on_deliverable_completed(
            deliverable_id="feature_b",
            agent="TesterAgent",
            phase="phase_1",
            description="Feature B completed with tests",
        )

        # Verify all agents logged
        log_file = parac_dir / "memory" / "logs" / "agent_actions.log"
        log_content = log_file.read_text()

        assert "ArchitectAgent" in log_content
        assert "CoderAgent" in log_content
        assert "TesterAgent" in log_content

        # Verify state shows 100% completion
        state_file = parac_dir / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        assert state["current_phase"]["progress"] == 100  # 2 of 2

    @pytest.mark.asyncio
    async def test_error_recovery_logging(self, temp_project, monkeypatch):
        """Test that failures are properly logged and handled."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        # Agent that fails
        @log_agent_action("CoderAgent", GovernanceActionType.BUGFIX)
        async def bugfix_with_error():
            await asyncio.sleep(0.01)
            raise RuntimeError("Bug fix failed")

        # Execute and expect failure
        with pytest.raises(RuntimeError, match="Bug fix failed"):
            await bugfix_with_error()

        # Verify failure was logged
        log_file = parac_dir / "memory" / "logs" / "agent_actions.log"
        log_content = log_file.read_text()

        assert "ERROR" in log_content  # Errors logged as ERROR type
        assert "FAILED" in log_content or "failed" in log_content.lower()

    @pytest.mark.asyncio
    async def test_context_manager_workflow(self, temp_project, monkeypatch):
        """Test workflow using context managers instead of decorators."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        state_manager = get_state_manager(parac_root=parac_dir)

        # Use context manager for operation
        async with async_agent_operation(
            "CoderAgent",
            "Implement feature using context manager",
            details={"action_type": "IMPLEMENTATION"},
        ):
            await asyncio.sleep(0.01)
            # Simulate implementation
            code = "def feature(): pass"

        # Mark complete
        await state_manager.on_deliverable_completed(
            deliverable_id="feature_a",
            agent="CoderAgent",
            phase="phase_1",
        )

        # Verify logging
        log_file = parac_dir / "memory" / "logs" / "agent_actions.log"
        log_content = log_file.read_text()

        assert "context manager" in log_content.lower()
        assert "CoderAgent" in log_content

    @pytest.mark.asyncio
    async def test_phase_transition(self, temp_project, monkeypatch):
        """Test complete phase with transition to next phase."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        state_manager = get_state_manager(parac_root=parac_dir)

        # Complete all deliverables
        await state_manager.on_deliverable_completed(
            deliverable_id="feature_a",
            agent="CoderAgent",
            phase="phase_1",
        )
        await state_manager.on_deliverable_completed(
            deliverable_id="feature_b",
            agent="CoderAgent",
            phase="phase_1",
        )

        # Complete phase
        await state_manager.on_phase_completed(
            phase_id="phase_1",
            phase_name="Development",
            agent="PMAgent",
        )

        # Verify phase completion
        state_file = parac_dir / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        assert state["current_phase"]["status"] == "completed"
        assert state["current_phase"]["progress"] == 100
        assert "completed_date" in state["current_phase"]

        # Start next phase
        await state_manager.on_phase_started(
            phase_id="phase_2",
            phase_name="Testing",
            agent="PMAgent",
        )

        # Verify phase transition
        with open(state_file) as f:
            state = yaml.safe_load(f)

        assert state["current_phase"]["id"] == "phase_2"
        assert state["current_phase"]["name"] == "Testing"
        assert state["previous_phase"]["id"] == "phase_1"


class TestConcurrency:
    """Test concurrent operations with automatic governance."""

    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self, temp_project, monkeypatch):
        """Test multiple agents executing concurrently."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        @log_agent_action("Worker", GovernanceActionType.IMPLEMENTATION)
        async def concurrent_task(task_id: int):
            await asyncio.sleep(0.01)
            return f"Task {task_id} complete"

        # Run 20 concurrent tasks
        tasks = [concurrent_task(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert all("complete" in r for r in results)

        # Verify all logged
        log_file = parac_dir / "memory" / "logs" / "agent_actions.log"
        log_content = log_file.read_text()

        # Should have 20 log entries
        assert log_content.count("Worker") >= 20

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self, temp_project, monkeypatch):
        """Test concurrent state updates are handled safely."""
        project_dir, parac_dir = temp_project
        monkeypatch.chdir(project_dir)

        state_manager = get_state_manager(parac_root=parac_dir)

        # Run 30 concurrent state updates
        tasks = [
            state_manager.on_deliverable_completed(
                deliverable_id=f"concurrent_{i}",
                agent=f"Agent{i % 5}",
                phase="phase_1",
            )
            for i in range(30)
        ]

        await asyncio.gather(*tasks)

        # Verify state file is still valid
        state_file = parac_dir / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Revision should be 31 (started at 1, incremented 30 times)
        assert state["revision"] == 31
        assert "current_phase" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
