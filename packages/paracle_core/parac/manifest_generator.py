"""Manifest generator for .parac/ workspace.

Generates manifest.yaml with agent metadata and workspace information.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from paracle_core.parac.agent_discovery import AgentDiscovery
from paracle_core.parac.state import load_state


class ManifestGenerator:
    """Generates .parac/manifest.yaml file."""

    SCHEMA_VERSION = "1.0"

    def __init__(self, parac_root: Path):
        """Initialize manifest generator.

        Args:
            parac_root: Root path of .parac/ directory
        """
        self.parac_root = parac_root
        self.discovery = AgentDiscovery(parac_root)

    def generate_manifest(self) -> dict[str, Any]:
        """Generate manifest data structure.

        Returns:
            Dictionary containing manifest data
        """
        # Discover agents
        agents = self.discovery.discover_agents()

        # Load project state for metadata
        state = load_state(self.parac_root)
        project_name = state.project_name if state else "unknown"
        project_version = state.project_version if state else "0.0.0"

        manifest = {
            "schema_version": self.SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "workspace": {
                "name": project_name,
                "version": project_version,
                "parac_version": "0.0.1",
                "root": str(self.parac_root),
            },
            "agents": [agent.to_dict() for agent in agents],
            "metadata": {
                "agent_count": len(agents),
                "specs_directory": "agents/specs/",
            },
        }

        return manifest

    def write_manifest(self, output_path: Path | None = None) -> Path:
        """Write manifest to file.

        Args:
            output_path: Optional custom output path.
                        If None, writes to .parac/manifest.yaml

        Returns:
            Path to written manifest file
        """
        if output_path is None:
            output_path = self.parac_root / "manifest.yaml"

        manifest = self.generate_manifest()

        # Write with nice formatting
        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(
                manifest,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        return output_path

    def get_manifest_json(self) -> str:
        """Get manifest as JSON string.

        Returns:
            JSON representation of manifest
        """
        import json

        manifest = self.generate_manifest()
        return json.dumps(manifest, indent=2)


def generate_manifest(parac_root: Path) -> dict[str, Any]:
    """Convenience function to generate manifest.

    Args:
        parac_root: Root path of .parac/ directory

    Returns:
        Dictionary containing manifest data
    """
    generator = ManifestGenerator(parac_root)
    return generator.generate_manifest()


def write_manifest(parac_root: Path, output_path: Path | None = None) -> Path:
    """Convenience function to write manifest file.

    Args:
        parac_root: Root path of .parac/ directory
        output_path: Optional custom output path

    Returns:
        Path to written manifest file
    """
    generator = ManifestGenerator(parac_root)
    return generator.write_manifest(output_path)
