"""Tests for tutorial command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner
from paracle_cli.commands.tutorial import (
    get_progress_file,
    load_progress,
    save_progress,
    tutorial,
)


@pytest.fixture
def runner():
    """Click CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace."""
    parac_dir = tmp_path / ".parac"
    parac_dir.mkdir()

    agents_dir = parac_dir / "agents" / "specs"
    agents_dir.mkdir(parents=True)

    memory_dir = parac_dir / "memory"
    memory_dir.mkdir()

    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=tmp_path):
        yield tmp_path


def test_get_progress_file(temp_workspace):
    """Test progress file path."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        progress_file = get_progress_file()
        assert progress_file.name == ".tutorial_progress.json"
        assert progress_file.parent.name == "memory"


def test_load_progress_new(temp_workspace):
    """Test loading progress when no file exists."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        progress = load_progress()

        assert progress["version"] == 1
        assert progress["last_step"] == 0
        assert "started" in progress
        assert len(progress["checkpoints"]) == 6
        assert all(
            status == "not_started" for status in progress["checkpoints"].values())


def test_save_and_load_progress(temp_workspace):
    """Test saving and loading progress."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # Create progress
        progress = {
            "version": 1,
            "started": "2026-01-07T10:00:00",
            "last_step": 2,
            "checkpoints": {
                "step_1": "completed",
                "step_2": "completed",
                "step_3": "not_started",
                "step_4": "not_started",
                "step_5": "not_started",
                "step_6": "not_started",
            },
        }

        # Save
        save_progress(progress)

        # Load
        loaded = load_progress()
        assert loaded["version"] == 1
        assert loaded["last_step"] == 2
        assert loaded["checkpoints"]["step_1"] == "completed"
        assert loaded["checkpoints"]["step_2"] == "completed"
        assert loaded["checkpoints"]["step_3"] == "not_started"


def test_tutorial_status_command(runner, temp_workspace):
    """Test tutorial status command."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        result = runner.invoke(tutorial, ["status"])

        assert result.exit_code == 0
        assert "Tutorial Progress" in result.output
        assert "Create your first agent" in result.output
        assert "Not Started" in result.output


def test_tutorial_status_with_progress(runner, temp_workspace):
    """Test tutorial status with saved progress."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # Save some progress
        progress = load_progress()
        progress["last_step"] = 2
        progress["checkpoints"]["step_1"] = "completed"
        progress["checkpoints"]["step_2"] = "completed"
        save_progress(progress)

        # Check status
        result = runner.invoke(tutorial, ["status"])

        assert result.exit_code == 0
        assert "Tutorial Progress" in result.output
        assert "Completed" in result.output


def test_tutorial_reset_command(runner, temp_workspace):
    """Test tutorial reset command."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # Create progress
        save_progress({"version": 1, "last_step": 3, "checkpoints": {}})

        # Reset (with confirmation)
        result = runner.invoke(tutorial, ["reset"], input="y\n")

        assert result.exit_code == 0
        assert "Tutorial progress reset" in result.output or "reset" in result.output.lower()


def test_tutorial_reset_cancelled(runner, temp_workspace):
    """Test tutorial reset cancellation."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # Create progress
        save_progress({"version": 1, "last_step": 3, "checkpoints": {}})
        progress_file = get_progress_file()

        # Cancel reset
        result = runner.invoke(tutorial, ["reset"], input="n\n")

        assert result.exit_code == 0
        assert progress_file.exists()  # File should still exist


def test_tutorial_help_command(runner):
    """Test tutorial help command."""
    result = runner.invoke(tutorial, ["--help"])

    assert result.exit_code == 0
    assert "Interactive tutorial" in result.output
    assert "start" in result.output
    assert "resume" in result.output
    assert "status" in result.output
    assert "reset" in result.output


def test_step_1_create_agent_dry_run(temp_workspace):
    """Test step 1 agent creation logic."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        from paracle_cli.commands.tutorial import step_1_create_agent

        progress = load_progress()

        # Mock user inputs and confirmations
        with patch("paracle_cli.commands.tutorial.Prompt.ask", side_effect=["test-agent", "Test description"]):
            with patch("paracle_cli.commands.tutorial.Confirm.ask", return_value=False):
                result = step_1_create_agent(progress)

                # Should save but not continue
                assert result is False
                assert progress["checkpoints"]["step_1"] == "completed"
                assert progress["last_step"] == 1

                # Check agent file created
                agent_file = temp_workspace / ".parac" / "agents" / "specs" / "test-agent.md"
                assert agent_file.exists()
                content = agent_file.read_text()
                assert "test-agent" in content
                assert "Test description" in content


def test_step_2_add_tools_dry_run(temp_workspace):
    """Test step 2 tools addition logic."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        from paracle_cli.commands.tutorial import step_2_add_tools

        # Create agent first
        agents_dir = temp_workspace / ".parac" / "agents" / "specs"
        agents_dir.mkdir(parents=True, exist_ok=True)
        agent_file = agents_dir / "test-agent.md"
        agent_file.write_text(
            "---\nname: test-agent\n---\n\n## Usage\n\nTest agent")

        progress = load_progress()

        # Mock user inputs
        with patch("paracle_cli.commands.tutorial.Prompt.ask", return_value="filesystem,http"):
            with patch("paracle_cli.commands.tutorial.Confirm.ask", return_value=False):
                result = step_2_add_tools(progress)

                # Should save but not continue
                assert result is False
                assert progress["checkpoints"]["step_2"] == "completed"
                assert progress["last_step"] == 2

                # Check tools added
                content = agent_file.read_text()
                assert "Tools" in content
                assert "filesystem" in content
                assert "http" in content


def test_progress_persistence(temp_workspace):
    """Test that progress persists across runs."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # First run - save progress
        progress1 = load_progress()
        progress1["last_step"] = 3
        progress1["checkpoints"]["step_1"] = "completed"
        progress1["checkpoints"]["step_2"] = "completed"
        progress1["checkpoints"]["step_3"] = "completed"
        save_progress(progress1)

        # Second run - load progress
        progress2 = load_progress()
        assert progress2["last_step"] == 3
        assert progress2["checkpoints"]["step_1"] == "completed"
        assert progress2["checkpoints"]["step_2"] == "completed"
        assert progress2["checkpoints"]["step_3"] == "completed"


def test_tutorial_start_command_from_beginning(runner, temp_workspace):
    """Test tutorial start from beginning (dry run)."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # Mock all user interactions to decline continuation
        with patch("paracle_cli.commands.tutorial.Confirm.ask", return_value=False):
            with patch("paracle_cli.commands.tutorial.Prompt.ask", side_effect=["my-agent", "Test agent"]):
                result = runner.invoke(tutorial, ["start"])

                # Should show welcome and start step 1
                assert "Welcome to Paracle" in result.output or result.exit_code == 0


def test_tutorial_resume_no_progress(runner, temp_workspace):
    """Test tutorial resume with no progress."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        result = runner.invoke(tutorial, ["resume"])

        assert result.exit_code == 0
        assert "No progress found" in result.output or "start" in result.output.lower()


def test_tutorial_resume_completed(runner, temp_workspace):
    """Test tutorial resume when already completed."""
    with patch("paracle_cli.commands.tutorial.Path.cwd", return_value=temp_workspace):
        # Save completed progress
        progress = load_progress()
        progress["last_step"] = 6
        progress["checkpoints"]["step_6"] = "completed"
        save_progress(progress)

        result = runner.invoke(tutorial, ["resume"])

        assert result.exit_code == 0
        assert "completed" in result.output.lower()
