"""IDE configuration generator for .parac/ integration.

Generates IDE-specific configuration files from .parac/ context
using Jinja2 templates. Also exports skills to platform-specific
formats (Agent Skills specification).
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
    # Categories: mcp_native, rules_based, web_based, cicd
    SUPPORTED_IDES: dict[str, IDEConfig] = {
        # === MCP Native IDEs ===
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
            display_name="Claude Code CLI",
            file_name="CLAUDE.md",
            template_name="claude.jinja2",
            destination_dir=".claude",
            max_context_size=50_000,
        ),
        "windsurf": IDEConfig(
            name="windsurf",
            display_name="Windsurf",
            file_name=".windsurfrules",
            template_name="windsurf.jinja2",
            destination_dir=".",
            max_context_size=50_000,
        ),
        "zed": IDEConfig(
            name="zed",
            display_name="Zed",
            file_name="ai_rules.json",
            template_name="zed.jinja2",
            destination_dir=".zed",
            max_context_size=50_000,
        ),
        # === Rules-based IDEs ===
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
        "warp": IDEConfig(
            name="warp",
            display_name="Warp Terminal",
            file_name="ai-rules.yaml",
            template_name="warp.jinja2",
            destination_dir=".warp",
            max_context_size=50_000,
        ),
        "gemini": IDEConfig(
            name="gemini",
            display_name="Gemini CLI",
            file_name="instructions.md",
            template_name="gemini.jinja2",
            destination_dir=".gemini",
            max_context_size=50_000,
        ),
        "opencode": IDEConfig(
            name="opencode",
            display_name="Opencode AI",
            file_name="rules.yaml",
            template_name="opencode.jinja2",
            destination_dir=".opencode",
            max_context_size=50_000,
        ),
        # === Web-based (copy-paste instructions) ===
        "claude_desktop": IDEConfig(
            name="claude_desktop",
            display_name="Claude.ai / Desktop",
            file_name="CLAUDE_INSTRUCTIONS.md",
            template_name="claude_desktop.jinja2",
            destination_dir=".",
            max_context_size=30_000,
        ),
        "chatgpt": IDEConfig(
            name="chatgpt",
            display_name="ChatGPT",
            file_name="CHATGPT_INSTRUCTIONS.md",
            template_name="chatgpt.jinja2",
            destination_dir=".",
            max_context_size=30_000,
        ),
        "raycast": IDEConfig(
            name="raycast",
            display_name="Raycast AI",
            file_name="raycast-ai-instructions.md",
            template_name="raycast.jinja2",
            destination_dir=".",
            max_context_size=30_000,
        ),
        # === CI/CD Integrations ===
        "claude_action": IDEConfig(
            name="claude_action",
            display_name="Claude Code GitHub Action",
            file_name="claude-code.yml",
            template_name="claude_action.jinja2",
            destination_dir=".github/workflows",
            max_context_size=10_000,
        ),
        "copilot_agent": IDEConfig(
            name="copilot_agent",
            display_name="GitHub Copilot Coding Agent",
            file_name="copilot-coding-agent.yml",
            template_name="copilot_agent.jinja2",
            destination_dir=".github",
            max_context_size=10_000,
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
                manifest["configs"].append(
                    {
                        "ide": ide,
                        "file": config.file_name,
                        "destination": f"{config.destination_dir}/{config.file_name}",
                        "exists": True,
                    }
                )

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
            project_file = (
                self.project_root / config.destination_dir / config.file_name
            )

            status["ides"][ide] = {
                "generated": ide_file.exists(),
                "copied": project_file.exists(),
                "generated_path": str(ide_file) if ide_file.exists() else None,
                "project_path": str(project_file) if project_file.exists() else None,
            }

        return status

    # =========================================================================
    # SKILL EXPORT METHODS
    # =========================================================================

    def export_skills(
        self,
        platforms: list[str] | None = None,
        overwrite: bool = False,
    ) -> dict[str, list[str]]:
        """Export skills to platform-specific formats.

        Exports skills from .parac/agents/skills/ to platform-specific
        directories following the Agent Skills specification.

        Args:
            platforms: Target platforms (default: all Agent Skills platforms)
            overwrite: Whether to overwrite existing files

        Returns:
            Dictionary mapping platform to list of exported skill names
        """
        try:
            from paracle_skills import SkillExporter, SkillLoader
            from paracle_skills.exporter import AGENT_SKILLS_PLATFORMS
        except ImportError:
            # paracle_skills not available
            return {}

        # Default to Agent Skills platforms (not MCP)
        if platforms is None:
            platforms = AGENT_SKILLS_PLATFORMS

        skills_dir = self.parac_root / "agents" / "skills"
        if not skills_dir.exists():
            return {}

        # Load skills
        loader = SkillLoader(skills_dir)
        try:
            skills = loader.load_all()
        except Exception:
            return {}

        if not skills:
            return {}

        # Export to each platform
        exporter = SkillExporter(skills)
        results = exporter.export_all(self.project_root, platforms, overwrite)

        # Build result dict
        exported: dict[str, list[str]] = {}
        for result in results:
            for platform, export_result in result.results.items():
                if export_result.success:
                    if platform not in exported:
                        exported[platform] = []
                    exported[platform].append(result.skill_name)

        return exported

    def export_skills_to_platform(
        self,
        platform: str,
        overwrite: bool = False,
    ) -> list[str]:
        """Export all skills to a single platform.

        Args:
            platform: Target platform (copilot, cursor, claude, codex, mcp)
            overwrite: Whether to overwrite existing files

        Returns:
            List of exported skill names
        """
        try:
            from paracle_skills import SkillExporter, SkillLoader
        except ImportError:
            return []

        skills_dir = self.parac_root / "agents" / "skills"
        if not skills_dir.exists():
            return []

        loader = SkillLoader(skills_dir)
        try:
            skills = loader.load_all()
        except Exception:
            return []

        if not skills:
            return []

        exporter = SkillExporter(skills)
        results = exporter.export_to_platform(platform, self.project_root, overwrite)

        return [r.skill_name for r in results if r.success]

    def sync_with_skills(
        self,
        platforms: list[str] | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Generate IDE configs and export skills together.

        This is the recommended method for complete IDE synchronization.

        Args:
            platforms: Skill export platforms (default: all)
            overwrite: Whether to overwrite existing skill files

        Returns:
            Dictionary with ide_configs and skills export results
        """
        results: dict[str, Any] = {
            "ide_configs": {},
            "skills": {},
            "errors": [],
        }

        # Generate IDE configs
        try:
            results["ide_configs"] = self.generate_all()
        except Exception as e:
            results["errors"].append(f"IDE config generation: {e}")

        # Export skills
        try:
            results["skills"] = self.export_skills(platforms, overwrite)
        except Exception as e:
            results["errors"].append(f"Skills export: {e}")

        return results
