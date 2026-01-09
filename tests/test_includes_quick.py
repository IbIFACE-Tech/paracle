"""Quick test for configuration include mechanism."""

import tempfile
from pathlib import Path

from paracle_core.parac.file_config import FileManagementConfig


def test_include_mechanism():
    """Test that include mechanism works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parac_root = Path(tmpdir) / ".parac"
        parac_root.mkdir()
        (parac_root / "config").mkdir()

        # Create project.yaml with include
        project_yaml = parac_root / "project.yaml"
        project_yaml.write_text(
            """
name: test-project
include:
  - config/logging.yaml
file_management:
  logs:
    base_path: original/logs
"""
        )

        # Create logging.yaml with custom settings
        logging_yaml = parac_root / "config" / "logging.yaml"
        logging_yaml.write_text(
            """
file_management:
  logs:
    base_path: custom/logs
    global:
      max_line_length: 1500
"""
        )

        # Load config
        config = FileManagementConfig.from_project_yaml(parac_root)

        # Verify settings from included file override base
        print("✓ Config loaded successfully")
        print(f"  logs.base_path: {config.logs.base_path}")
        print(
            f"  logs.global.max_line_length: {config.logs.global_config.max_line_length}"
        )

        assert (
            config.logs.base_path == "custom/logs"
        ), f"Expected 'custom/logs', got '{config.logs.base_path}'"
        assert (
            config.logs.global_config.max_line_length == 1500
        ), f"Expected 1500, got {config.logs.global_config.max_line_length}"

        print("\n✅ Include mechanism works correctly!")


if __name__ == "__main__":
    test_include_mechanism()
