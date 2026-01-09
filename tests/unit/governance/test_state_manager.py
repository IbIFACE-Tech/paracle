"""Unit tests for automatic state management."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml
from paracle_core.governance.state_manager import (
    AutomaticStateManager,
    get_state_manager,
)


class TestAutomaticStateManager:
    """Tests for AutomaticStateManager."""

    @pytest.fixture
    def temp_parac(self):
        """Create temporary .parac structure with state files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parac_dir = Path(tmpdir) / ".parac"

            # Create directories
            context_dir = parac_dir / "memory" / "context"
            roadmap_dir = parac_dir / "roadmap"
            context_dir.mkdir(parents=True)
            roadmap_dir.mkdir(parents=True)

            # Create initial current_state.yaml
            state_file = context_dir / "current_state.yaml"
            initial_state = {
                "project": {
                    "name": "test-project",
                    "version": "0.1.0",
                },
                "current_phase": {
                    "id": "phase_1",
                    "name": "Foundation",
                    "status": "in_progress",
                    "progress": 50,
                    "completed": ["deliverable_1"],
                    "in_progress": ["deliverable_2"],
                },
                "recent_updates": [],
                "revision": 1,
            }
            state_file.write_text(yaml.dump(initial_state))

            # Create roadmap.yaml
            roadmap_file = roadmap_dir / "roadmap.yaml"
            roadmap = {
                "phases": [
                    {
                        "id": "phase_1",
                        "name": "Foundation",
                        "status": "in_progress",
                        "deliverables": [
                            {
                                "id": "deliverable_1",
                                "name": "Setup",
                                "status": "completed",
                            },
                            {
                                "id": "deliverable_2",
                                "name": "Implementation",
                                "status": "in_progress",
                            },
                            {
                                "id": "deliverable_3",
                                "name": "Testing",
                                "status": "not_started",
                            },
                        ],
                    }
                ]
            }
            roadmap_file.write_text(yaml.dump(roadmap))

            yield parac_dir

    @pytest.mark.asyncio
    async def test_on_deliverable_completed(self, temp_parac):
        """Test that completing a deliverable updates state."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        await manager.on_deliverable_completed(
            deliverable_id="deliverable_2",
            agent="TestAgent",
            phase="phase_1",
            description="Implemented feature X",
        )

        # Read updated state
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Verify deliverable marked complete
        assert "deliverable_2" in state["current_phase"]["completed"]
        assert "deliverable_2" not in state["current_phase"]["in_progress"]

        # Verify progress updated (2 of 3 = 66% due to int truncation)
        assert state["current_phase"]["progress"] == 66

        # Verify recent update added
        assert len(state["recent_updates"]) > 0
        latest_update = state["recent_updates"][0]
        assert "deliverable_2" in latest_update["update"]
        assert latest_update["agent"] == "TestAgent"

        # Verify revision incremented
        assert state["revision"] == 2

    @pytest.mark.asyncio
    async def test_on_phase_started(self, temp_parac):
        """Test starting a new phase."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        await manager.on_phase_started(
            phase_id="phase_2",
            phase_name="Development",
            agent="PMAgent",
        )

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Verify current phase updated
        assert state["current_phase"]["id"] == "phase_2"
        assert state["current_phase"]["name"] == "Development"
        assert state["current_phase"]["status"] == "in_progress"
        assert state["current_phase"]["progress"] == 0

        # Verify previous phase recorded
        assert state["previous_phase"]["id"] == "phase_1"
        assert state["previous_phase"]["status"] == "in_progress"

        # Verify recent update added
        assert len(state["recent_updates"]) > 0
        latest_update = state["recent_updates"][0]
        has_phase_info = (
            "phase_2" in latest_update["impact"]
            or "Development" in latest_update["update"]
        )
        assert has_phase_info
        assert latest_update["agent"] == "PMAgent"

    @pytest.mark.asyncio
    async def test_on_phase_completed(self, temp_parac):
        """Test completing a phase."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        await manager.on_phase_completed(
            phase_id="phase_1",
            phase_name="Foundation",
            agent="PMAgent",
        )

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Verify phase marked complete
        assert state["current_phase"]["status"] == "completed"
        assert state["current_phase"]["progress"] == 100

        # Verify completion date added
        assert "completed_date" in state["current_phase"]

        # Verify recent update added
        assert len(state["recent_updates"]) > 0
        latest_update = state["recent_updates"][0]
        has_completion_info = (
            "phase_1" in latest_update["impact"]
            or "COMPLETE" in latest_update["update"]
        )
        assert has_completion_info

    @pytest.mark.asyncio
    async def test_progress_calculation(self, temp_parac):
        """Test that progress is calculated correctly."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        # Complete deliverable_2
        await manager.on_deliverable_completed(
            deliverable_id="deliverable_2",
            agent="TestAgent",
            phase="phase_1",
        )

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # 2 of 3 deliverables = 66% (int truncation)
        assert state["current_phase"]["progress"] == 66

        # Complete deliverable_3
        await manager.on_deliverable_completed(
            deliverable_id="deliverable_3",
            agent="TestAgent",
            phase="phase_1",
        )

        with open(state_file) as f:
            state = yaml.safe_load(f)

        # 3 of 3 deliverables = 100%
        assert state["current_phase"]["progress"] == 100

    @pytest.mark.asyncio
    async def test_recent_updates_limit(self, temp_parac):
        """Test that recent_updates list is limited to 20 entries."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        # Add 25 updates
        for i in range(25):
            await manager.on_deliverable_completed(
                deliverable_id=f"deliverable_{i}",
                agent="TestAgent",
                phase="phase_1",
                description=f"Update {i}",
            )

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Should only keep 20 most recent
        assert len(state["recent_updates"]) == 20

        # Latest update should be update 24 (in 'impact' field)
        latest = state["recent_updates"][0]
        assert "Update 24" in latest["impact"]

    @pytest.mark.asyncio
    async def test_atomic_write(self, temp_parac):
        """Test that state writes are atomic."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        state_file = temp_parac / "memory" / "context" / "current_state.yaml"

        # Simulate concurrent updates
        tasks = []
        for i in range(10):
            task = manager.on_deliverable_completed(
                deliverable_id=f"concurrent_{i}",
                agent="TestAgent",
                phase="phase_1",
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        # File should still be valid YAML
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # All updates should be recorded
        assert state["revision"] == 11  # Started at 1, incremented 10 times

    @pytest.mark.asyncio
    async def test_error_handling_missing_phase(self, temp_parac):
        """Test handling of missing phase in roadmap."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        # Try to complete deliverable in non-existent phase
        await manager.on_deliverable_completed(
            deliverable_id="deliverable_2",
            agent="TestAgent",
            phase="phase_999",  # Doesn't exist
        )

        # Should not crash - just skip roadmap update
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # State should still be updated
        assert state["revision"] == 2

    @pytest.mark.asyncio
    async def test_error_handling_missing_deliverable(self, temp_parac):
        """Test handling of missing deliverable in roadmap."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        # Try to complete non-existent deliverable
        await manager.on_deliverable_completed(
            deliverable_id="deliverable_999",  # Doesn't exist
            agent="TestAgent",
            phase="phase_1",
        )

        # Should not crash
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # State should still be updated
        assert state["revision"] == 2


class TestGetStateManager:
    """Tests for get_state_manager singleton."""

    def test_singleton_instance(self):
        """Test that get_state_manager returns same instance."""
        manager1 = get_state_manager()
        manager2 = get_state_manager()

        assert manager1 is manager2

    def test_custom_parac_root(self, tmp_path):
        """Test that custom parac_root is respected."""
        from paracle_core.governance.state_manager import reset_state_manager

        # Reset to ensure we get a fresh instance
        reset_state_manager()

        parac_dir = tmp_path / ".parac"
        parac_dir.mkdir()

        manager = get_state_manager(parac_root=parac_dir)

        assert manager.parac_root == parac_dir

        # Reset for other tests
        reset_state_manager()


class TestThreadSafety:
    """Tests for thread safety of state manager."""

    @pytest.fixture
    def temp_parac(self):
        """Create temporary .parac structure with state files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parac_dir = Path(tmpdir) / ".parac"

            # Create directories
            context_dir = parac_dir / "memory" / "context"
            roadmap_dir = parac_dir / "roadmap"
            context_dir.mkdir(parents=True)
            roadmap_dir.mkdir(parents=True)

            # Create initial current_state.yaml
            state_file = context_dir / "current_state.yaml"
            initial_state = {
                "project": {
                    "name": "test-project",
                    "version": "0.1.0",
                },
                "current_phase": {
                    "id": "phase_1",
                    "name": "Foundation",
                    "status": "in_progress",
                    "progress": 50,
                    "completed": ["deliverable_1"],
                    "in_progress": ["deliverable_2"],
                },
                "recent_updates": [],
                "revision": 1,
            }
            state_file.write_text(yaml.dump(initial_state))

            # Create roadmap.yaml
            roadmap_file = roadmap_dir / "roadmap.yaml"
            roadmap = {
                "phases": [
                    {
                        "id": "phase_1",
                        "name": "Foundation",
                        "status": "in_progress",
                        "deliverables": [
                            {
                                "id": "deliverable_1",
                                "name": "Setup",
                                "status": "completed",
                            },
                            {
                                "id": "deliverable_2",
                                "name": "Implementation",
                                "status": "in_progress",
                            },
                            {
                                "id": "deliverable_3",
                                "name": "Testing",
                                "status": "not_started",
                            },
                        ],
                    }
                ]
            }
            roadmap_file.write_text(yaml.dump(roadmap))

            yield parac_dir

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, temp_parac):
        """Test that concurrent updates are handled safely."""
        manager = AutomaticStateManager(parac_root=temp_parac)

        # Run 50 concurrent updates
        tasks = []
        for i in range(50):
            task = manager.on_deliverable_completed(
                deliverable_id=f"concurrent_{i}",
                agent=f"Agent{i % 5}",
                phase="phase_1",
                description=f"Concurrent update {i}",
            )
            tasks.append(task)

        # All should complete without error
        await asyncio.gather(*tasks)

        # Verify final state is consistent
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        with open(state_file) as f:
            state = yaml.safe_load(f)

        # Revision should be 51 (started at 1, incremented 50 times)
        assert state["revision"] == 51

        # YAML file should be valid (not corrupted)
        assert "current_phase" in state
        assert "recent_updates" in state


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.fixture
    def temp_parac(self):
        """Create temporary .parac structure with state files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parac_dir = Path(tmpdir) / ".parac"

            # Create directories
            context_dir = parac_dir / "memory" / "context"
            roadmap_dir = parac_dir / "roadmap"
            context_dir.mkdir(parents=True)
            roadmap_dir.mkdir(parents=True)

            # Create initial current_state.yaml
            state_file = context_dir / "current_state.yaml"
            initial_state = {
                "project": {
                    "name": "test-project",
                    "version": "0.1.0",
                },
                "current_phase": {
                    "id": "phase_1",
                    "name": "Foundation",
                    "status": "in_progress",
                    "progress": 50,
                    "completed": ["deliverable_1"],
                    "in_progress": ["deliverable_2"],
                },
                "recent_updates": [],
                "revision": 1,
            }
            state_file.write_text(yaml.dump(initial_state))

            # Create roadmap.yaml
            roadmap_file = roadmap_dir / "roadmap.yaml"
            roadmap = {
                "phases": [
                    {
                        "id": "phase_1",
                        "name": "Foundation",
                        "status": "in_progress",
                        "deliverables": [
                            {
                                "id": "deliverable_1",
                                "name": "Setup",
                                "status": "completed",
                            },
                            {
                                "id": "deliverable_2",
                                "name": "Implementation",
                                "status": "in_progress",
                            },
                            {
                                "id": "deliverable_3",
                                "name": "Testing",
                                "status": "not_started",
                            },
                        ],
                    }
                ]
            }
            roadmap_file.write_text(yaml.dump(roadmap))

            yield parac_dir

    @pytest.mark.asyncio
    async def test_missing_parac_directory(self):
        """Test handling of missing .parac directory."""
        manager = AutomaticStateManager(parac_root=Path("/nonexistent/.parac"))
        # The error is raised when trying to load files, not on construction
        with pytest.raises(FileNotFoundError):
            await manager.on_deliverable_completed(
                deliverable_id="test",
                agent="TestAgent",
                phase="phase_1",
            )

    @pytest.mark.asyncio
    async def test_empty_state_file(self, temp_parac):
        """Test handling of empty state file."""
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        state_file.write_text("")

        manager = AutomaticStateManager(parac_root=temp_parac)

        # Empty YAML returns None, which will cause TypeError when accessing keys
        # This tests the graceful handling expectation
        with pytest.raises((TypeError, AttributeError)):
            await manager.on_deliverable_completed(
                deliverable_id="test",
                agent="TestAgent",
                phase="phase_1",
            )

    @pytest.mark.asyncio
    async def test_malformed_yaml(self, temp_parac):
        """Test handling of malformed YAML."""
        state_file = temp_parac / "memory" / "context" / "current_state.yaml"
        state_file.write_text("{ invalid yaml ][")

        manager = AutomaticStateManager(parac_root=temp_parac)

        # Malformed YAML will raise yaml.YAMLError
        with pytest.raises(yaml.YAMLError):
            await manager.on_deliverable_completed(
                deliverable_id="test",
                agent="TestAgent",
                phase="phase_1",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
