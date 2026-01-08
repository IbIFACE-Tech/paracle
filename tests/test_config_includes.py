"""Test configuration include mechanism.

This test verifies that the split configuration system works correctly:
1. project-minimal.yaml loads successfully
2. Include directives merge config files
3. Deep merge preserves values correctly
"""

import tempfile
from pathlib import Path

import pytest
from paracle_core.parac.file_config import FileManagementConfig


@pytest.fixture
def temp_parac():
    """Create temporary .parac/ directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        parac_root = Path(tmpdir) / ".parac"
        parac_root.mkdir()
        (parac_root / "config").mkdir()
        yield parac_root


def test_minimal_config_loads(temp_parac):
    """Test that minimal config (no includes) loads successfully."""
    # Create minimal project.yaml
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
version: 0.1.0
defaults:
  model_provider: openai
  default_model: gpt-4o-mini
"""
    )

    # Load config (should use defaults)
    config = FileManagementConfig.from_project_yaml(temp_parac)

    assert config is not None
    assert config.logs.base_path == "memory/logs"
    assert config.adr.base_path == "roadmap/adr"


def test_include_single_file(temp_parac):
    """Test including single config file merges correctly."""
    # Create project.yaml with include
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
include:
  - config/logging.yaml
"""
    )

    # Create logging.yaml with custom settings
    logging_yaml = temp_parac / "config" / "logging.yaml"
    logging_yaml.write_text(
        """
file_management:
  logs:
    base_path: custom/logs
    global:
      max_line_length: 1500
      max_file_size_mb: 75
"""
    )

    # Load config
    config = FileManagementConfig.from_project_yaml(temp_parac)

    # Verify settings from included file
    assert config.logs.base_path == "custom/logs"
    assert config.logs.global_config.max_line_length == 1500
    assert config.logs.global_config.max_file_size_mb == 75


def test_include_multiple_files(temp_parac):
    """Test including multiple config files merges correctly."""
    # Create project.yaml with multiple includes
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
include:
  - config/logging.yaml
  - config/file-management.yaml
"""
    )

    # Create logging.yaml
    logging_yaml = temp_parac / "config" / "logging.yaml"
    logging_yaml.write_text(
        """
file_management:
  logs:
    base_path: custom/logs
    global:
      max_line_length: 1500
"""
    )

    # Create file-management.yaml (includes ADR config)
    file_mgmt_yaml = temp_parac / "config" / "file-management.yaml"
    file_mgmt_yaml.write_text(
        """
file_management:
  adr:
    base_path: custom/adr
    limits:
      max_title_length: 150
"""
    )

    # Load config
    config = FileManagementConfig.from_project_yaml(temp_parac)

    # Verify both includes merged
    assert config.logs.base_path == "custom/logs"
    assert config.logs.global_config.max_line_length == 1500
    assert config.adr.base_path == "custom/adr"
    assert config.adr.limits.max_title_length == 150


def test_include_missing_file(temp_parac):
    """Test that missing include files are skipped gracefully."""
    # Create project.yaml referencing non-existent file
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
include:
  - config/nonexistent.yaml
  - config/also-missing.yaml
"""
    )

    # Load config (should not fail, use defaults)
    config = FileManagementConfig.from_project_yaml(temp_parac)

    assert config is not None
    assert config.logs.base_path == "memory/logs"


def test_deep_merge_nested_dicts(temp_parac):
    """Test that deep merge preserves nested structures."""
    # Create project.yaml with base settings
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
file_management:
  logs:
    global:
      max_line_length: 1000
      max_file_size_mb: 50
include:
  - config/logging.yaml
"""
    )

    # Create logging.yaml that overrides only max_file_size_mb
    logging_yaml = temp_parac / "config" / "logging.yaml"
    logging_yaml.write_text(
        """
file_management:
  logs:
    global:
      max_file_size_mb: 100
"""
    )

    # Load config
    config = FileManagementConfig.from_project_yaml(temp_parac)

    # Verify deep merge: max_line_length preserved, max_file_size_mb overridden
    assert config.logs.global_config.max_line_length == 1000
    assert config.logs.global_config.max_file_size_mb == 100


def test_split_config_like_project_minimal(temp_parac):
    """Test realistic scenario: project-minimal.yaml + optional configs."""
    # Create project-minimal.yaml
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: my-project
version: 0.1.0
description: Test project using split configuration

defaults:
  model_provider: openai
  default_model: gpt-4o-mini

include:
  - config/logging.yaml
  - config/file-management.yaml
"""
    )

    # Create logging.yaml (enterprise settings)
    logging_yaml = temp_parac / "config" / "logging.yaml"
    logging_yaml.write_text(
        """
file_management:
  logs:
    base_path: memory/logs
    global:
      max_line_length: 1000
      max_file_size_mb: 50
      async_logging: true
"""
    )

    # Create file-management.yaml (log categories + ADR)
    file_mgmt_yaml = temp_parac / "config" / "file-management.yaml"
    file_mgmt_yaml.write_text(
        """
file_management:
  logs:
    predefined:
      actions:
        enabled: true
        path: agent_actions.log
        max_line_length: 800
        max_file_size_mb: 25
      decisions:
        enabled: true
        path: decisions.log
        max_line_length: 1200
  adr:
    enabled: true
    base_path: roadmap/adr
    limits:
      max_title_length: 120
      max_total_length: 15000
"""
    )

    # Load config
    config = FileManagementConfig.from_project_yaml(temp_parac)

    # Verify merged configuration
    assert config.logs.base_path == "memory/logs"
    assert config.logs.global_config.max_line_length == 1000
    assert config.logs.global_config.async_logging is True
    assert config.logs.predefined.actions.enabled is True
    assert config.logs.predefined.actions.max_line_length == 800
    assert config.logs.predefined.decisions.max_line_length == 1200
    assert config.adr.enabled is True
    assert config.adr.limits.max_title_length == 120


def test_no_include_section(temp_parac):
    """Test config without include section works normally."""
    # Create project.yaml without includes
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
file_management:
  logs:
    base_path: custom/logs
"""
    )

    # Load config
    config = FileManagementConfig.from_project_yaml(temp_parac)

    assert config.logs.base_path == "custom/logs"


def test_include_override_order(temp_parac):
    """Test that later includes override earlier ones."""
    # Create project.yaml
    project_yaml = temp_parac / "project.yaml"
    project_yaml.write_text(
        """
name: test-project
include:
  - config/first.yaml
  - config/second.yaml
"""
    )

    # First config sets value to 100
    first_yaml = temp_parac / "config" / "first.yaml"
    first_yaml.write_text(
        """
file_management:
  logs:
    global:
      max_file_size_mb: 100
"""
    )

    # Second config overrides to 200
    second_yaml = temp_parac / "config" / "second.yaml"
    second_yaml.write_text(
        """
file_management:
  logs:
    global:
      max_file_size_mb: 200
"""
    )

    # Load config
    config = FileManagementConfig.from_project_yaml(temp_parac)

    # Last include wins
    assert config.logs.global_config.max_file_size_mb == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
