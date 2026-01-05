"""IDE configuration generator for .parac/ integration.

Generates IDE-specific configuration files from .parac/ context
using Jinja2 templates.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from paracle_core.parac.context_builder import ContextBuilder


@dataclass
class IDEConfig:
    """Configuration for a specific IDE."""

    name: str
    display_name: str
    file_name: str
    template_name: str
    destination_dir: str  # Relative to project root
    max_context_size: int = 50_000


class IDEConfigGenerator:
    """Generates IDE-specific configuration files from .parac/ context.

    Uses Jinja2 templates to render IDE configuration files with
    embedded .parac/ context.
    """

    # Supported IDEs with their configurations
    SUPPORTED_IDES: dict[str, IDEConfig] = {
        "cursor": IDEConfig(
            name="cursor",
            display_name="Cursor",
            file_name=".cursorrules",
            template_name="cursor.jinja2",
            destination_dir=".",
            max_context_size=100_000,
        ),
        "claude": IDEConfig(
            name="claude",
            display_name="Claude Code",
            file_name="CLAUDE.md",
            template_name="claude.jinja2",
            destination_dir=".claude",
            max_context_size=50_000,
        ),
        "cline": IDEConfig(
            name="cline",
            display_name="Cline",
            file_name=".clinerules",
            template_name="cline.jinja2",
            destination_dir=".",
            max_context_size=50_000,
        ),
        "copilot": IDEConfig(
            name="copilot",
            display_name="GitHub Copilot",
            file_name="copilot-instructions.md",
            template_name="copilot.jinja2",
            destination_dir=".github",
            max_context_size=30_000,
        ),
        "windsurf": IDEConfig(
            name="windsurf",
            display_name="Windsurf",
            file_name=".windsurfrules",
            template_name="windsurf.jinja2",
            destination_dir=".",
            max_context_size=50_000,
        ),
    }

    def __init__(self, parac_root: Path, project_root: Path | None = None):
        """Initialize IDE config generator.

        Args:
            parac_root: Path to .parac/ directory
            project_root: Path to project root (defaults to parac_root parent)
        """
        self.parac_root = parac_root
        self.project_root = project_root or parac_root.parent
        self.ide_output_dir = parac_root / "integrations" / "ide"
        self._jinja_env = None

    def _get_jinja_env(self) -> Any:
        """Get or create Jinja2 environment."""
        if self._jinja_env is not None:
            return self._jinja_env

        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
        except ImportError as e:
            raise ImportError(
                "jinja2 is required for IDE config generation. "
                "Install with: pip install jinja2"
            ) from e

        # Template directory
        templates_dir = Path(__file__).parent.parent / "templates" / "ide"
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)

        self._jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._jinja_env.filters["yaml_format"] = self._yaml_format_filter

        return self._jinja_env

    def _yaml_format_filter(self, value: Any) -> str:
        """Jinja2 filter to format value as YAML."""
        return yaml.dump(value, default_flow_style=False, allow_unicode=True)

    def get_supported_ides(self) -> list[str]:
        """Get list of supported IDE names."""
        return list(self.SUPPORTED_IDES.keys())

    def get_ide_config(self, ide: str) -> IDEConfig | None:
        """Get configuration for a specific IDE."""
        return self.SUPPORTED_IDES.get(ide.lower())

    def generate(self, ide: str) -> str:
        """Generate IDE configuration content.

        Args:
            ide: Target IDE name

        Returns:
            Generated configuration content

        Raises:
            ValueError: If IDE is not supported
            FileNotFoundError: If template is not found
        """
        config = self.get_ide_config(ide)
        if not config:
            raise ValueError(
                f"Unsupported IDE: {ide}. "
                f"Supported: {', '.join(self.get_supported_ides())}"
            )

        # Build context
        builder = ContextBuilder(self.parac_root, max_size=config.max_context_size)
        context = builder.build(ide=config.name)

        # Add IDE-specific context
        context["ide_config"] = {
            "name": config.name,
            "display_name": config.display_name,
            "file_name": config.file_name,
        }

        # Render template
        env = self._get_jinja_env()

        try:
            template = env.get_template(config.template_name)
        except Exception:
            # Fall back to base template if specific template not found
            template = env.get_template("base.jinja2")

        return template.render(**context)

    def generate_to_file(self, ide: str, output_dir: Path | None = None) -> Path:
        """Generate IDE config and write to file.

        Args:
            ide: Target IDE name
            output_dir: Output directory (defaults to .parac/integrations/ide/)

        Returns:
            Path to generated file
        """
        config = self.get_ide_config(ide)
        if not config:
            raise ValueError(f"Unsupported IDE: {ide}")

        # Generate content
        content = self.generate(ide)

        # Determine output path
        if output_dir is None:
            output_dir = self.ide_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / config.file_name
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_all(self, output_dir: Path | None = None) -> dict[str, Path]:
        """Generate configs for all supported IDEs.

        Args:
            output_dir: Output directory (defaults to .parac/integrations/ide/)

        Returns:
            Dictionary mapping IDE name to generated file path
        """
        results = {}
        for ide in self.SUPPORTED_IDES:
            try:
                path = self.generate_to_file(ide, output_dir)
                results[ide] = path
            except Exception as e:
                # Log error but continue with other IDEs
                print(f"Warning: Failed to generate {ide} config: {e}")

        return results

    def copy_to_project(self, ide: str) -> Path:
        """Copy generated config to project root.

        Args:
            ide: Target IDE name

        Returns:
            Path to copied file in project root
        """
        config = self.get_ide_config(ide)
        if not config:
            raise ValueError(f"Unsupported IDE: {ide}")

        # Source file in .parac/integrations/ide/
        source = self.ide_output_dir / config.file_name
        if not source.exists():
            # Generate if not exists
            self.generate_to_file(ide)

        # Destination in project root
        dest_dir = self.project_root / config.destination_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / config.file_name

        # Copy content
        content = source.read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")

        return dest

    def copy_all_to_project(self) -> dict[str, Path]:
        """Copy all generated configs to project root.

        Returns:
            Dictionary mapping IDE name to copied file path
        """
        results = {}
        for ide in self.SUPPORTED_IDES:
            try:
                path = self.copy_to_project(ide)
                results[ide] = path
            except Exception as e:
                print(f"Warning: Failed to copy {ide} config: {e}")

        return results

    def generate_manifest(self) -> Path:
        """Generate manifest file tracking generated configs.

        Returns:
            Path to manifest file
        """
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "0.0.1",
            "parac_root": str(self.parac_root),
            "configs": [],
        }

        for ide, config in self.SUPPORTED_IDES.items():
            ide_file = self.ide_output_dir / config.file_name
            if ide_file.exists():
                manifest["configs"].append({
                    "ide": ide,
                    "file": config.file_name,
                    "destination": f"{config.destination_dir}/{config.file_name}",
                    "exists": True,
                })

        manifest_path = self.ide_output_dir / "_manifest.yaml"
        self.ide_output_dir.mkdir(parents=True, exist_ok=True)

        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True)

        return manifest_path

    def get_status(self) -> dict[str, Any]:
        """Get status of IDE integration.

        Returns:
            Dictionary with status information
        """
        status = {
            "parac_root": str(self.parac_root),
            "project_root": str(self.project_root),
            "ide_output_dir": str(self.ide_output_dir),
            "ides": {},
        }

        for ide, config in self.SUPPORTED_IDES.items():
            ide_file = self.ide_output_dir / config.file_name
            project_file = self.project_root / config.destination_dir / config.file_name

            status["ides"][ide] = {
                "generated": ide_file.exists(),
                "copied": project_file.exists(),
                "generated_path": str(ide_file) if ide_file.exists() else None,
                "project_path": str(project_file) if project_file.exists() else None,
            }

        return status
