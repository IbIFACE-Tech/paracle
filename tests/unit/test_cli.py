"""Unit tests for CLI."""

from click.testing import CliRunner
from paracle_cli.main import cli


class TestCLI:
    """Tests for CLI commands."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Paracle" in result.output

    def test_hello_command(self) -> None:
        """Test hello command."""
        result = self.runner.invoke(cli, ["hello"])
        assert result.exit_code == 0
        assert "Hello World" in result.output
        assert "0.0.1" in result.output

    def test_agent_create_placeholder(self) -> None:
        """Test agent create placeholder."""
        result = self.runner.invoke(cli, ["agent", "create", "test-agent"])
        assert result.exit_code == 0
        assert "test-agent" in result.output

    def test_workflow_run_placeholder(self) -> None:
        """Test workflow run placeholder."""
        result = self.runner.invoke(cli, ["workflow", "run", "test-workflow"])
        assert result.exit_code == 0
        assert "test-workflow" in result.output
