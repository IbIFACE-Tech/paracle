"""IDE configuration generator for .parac/ integration.

Generates IDE-specific configuration files from .parac/ context
using Jinja2 templates. Also exports skills to platform-specific
formats (Agent Skills specification).

Ensures .parac/ is validated and formatted before generation to
maintain it as the single source of truth.
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


@dataclass
class MCPConfig:
    """MCP configuration for a specific IDE/tool.

    Different IDEs have different MCP configuration formats and locations.
    """

    name: str
    display_name: str
    file_name: str
    destination_dir: str  # Relative to project root or home
    config_format: str  # "json" or "yaml"
    uses_home_dir: bool = False  # If True, destination is relative to ~
    server_key: str = "mcpServers"  # Key name for servers object


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
        "rovodev": IDEConfig(
            name="rovodev",
            display_name="Atlassian Rovo Dev",
            file_name="config.yml",
            template_name="rovodev.jinja2",
            destination_dir=".rovodev",
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

    # MCP configurations for IDEs that support Model Context Protocol
    # These define how to generate mcp.json/mcp_config.json for each IDE
    SUPPORTED_MCP: dict[str, MCPConfig] = {
        # === VS Code based ===
        "vscode": MCPConfig(
            name="vscode",
            display_name="VS Code / Copilot",
            file_name="mcp.json",
            destination_dir=".vscode",
            config_format="json",
        ),
        "cursor": MCPConfig(
            name="cursor",
            display_name="Cursor",
            file_name="mcp.json",
            destination_dir=".cursor",
            config_format="json",
        ),
        "cline": MCPConfig(
            name="cline",
            display_name="Cline",
            file_name="mcp.json",
            destination_dir=".cline",
            config_format="json",
        ),
        # === Other IDEs ===
        "windsurf": MCPConfig(
            name="windsurf",
            display_name="Windsurf",
            file_name="mcp_config.json",
            destination_dir=".codeium/windsurf",
            config_format="json",
            uses_home_dir=True,
        ),
        "claude_desktop": MCPConfig(
            name="claude_desktop",
            display_name="Claude Desktop",
            file_name="claude_desktop_config.json",
            destination_dir="Claude",
            config_format="json",
            uses_home_dir=True,
        ),
        "zed": MCPConfig(
            name="zed",
            display_name="Zed",
            file_name="mcp.json",
            destination_dir=".zed",
            config_format="json",
        ),
        "rovodev": MCPConfig(
            name="rovodev",
            display_name="Rovo Dev",
            file_name="mcp_config.json",
            destination_dir=".rovodev",
            config_format="json",
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
        self._workspace_prepared = False
        self._preparation_warnings: list[str] = []

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

    def _prepare_workspace(
        self, skip_format: bool = False, strict: bool = False
    ) -> None:
        """Validate and format .parac/ workspace before generation.

        Ensures .parac/ is the correct single source of truth by:
        1. Validating workspace structure and YAML files
        2. Formatting and validating all agent specs

        Args:
            skip_format: If True, skip formatting (only validate)
            strict: If True, treat warnings as errors

        Raises:
            ValueError: If validation fails or workspace is invalid
        """
        if self._workspace_prepared:
            return  # Already prepared

        self._preparation_warnings = []

        # Step 1: Validate .parac/ workspace structure
        try:
            from paracle_core.parac.validator import ParacValidator

            validator = ParacValidator(self.parac_root)
            result = validator.validate()

            if result.errors:
                error_msg = "Invalid .parac/ workspace:\n"
                for error in result.errors:
                    error_msg += f"  - {error}\n"
                raise ValueError(error_msg)

            if result.warnings:
                for warning in result.warnings:
                    self._preparation_warnings.append(str(warning))

                if strict:
                    warning_msg = "Workspace has warnings (strict mode):\n"
                    for warning in result.warnings:
                        warning_msg += f"  - {warning}\n"
                    raise ValueError(warning_msg)

        except ImportError:
            # Validator not available - continue with warning
            self._preparation_warnings.append(
                "Workspace validation skipped (validator not available)"
            )

        # Step 2: Format and validate agent specs
        specs_dir = self.parac_root / "agents" / "specs"
        if specs_dir.exists() and not skip_format:
            try:
                from paracle_core.agents.formatter import AgentSpecFormatter

                formatter = AgentSpecFormatter()
                format_results = formatter.format_directory(
                    specs_dir, fix=True, dry_run=False
                )

                # Check for validation errors
                errors = []
                warnings = []
                modified_count = 0

                for agent_id, (
                    validation_result,
                    was_modified,
                ) in format_results.items():
                    if was_modified:
                        modified_count += 1

                    if not validation_result.valid:
                        for error in validation_result.errors:
                            errors.append(f"{agent_id}: {error}")

                    # Collect warnings
                    if hasattr(validation_result, "warnings"):
                        for warning in validation_result.warnings:
                            warnings.append(f"{agent_id}: {warning}")

                if errors:
                    error_msg = "Invalid agent specifications:\n"
                    for error in errors:
                        error_msg += f"  - {error}\n"
                    raise ValueError(error_msg)

                # Track modifications and warnings
                if modified_count > 0:
                    self._preparation_warnings.append(
                        f"Auto-formatted {modified_count} agent spec(s)"
                    )

                self._preparation_warnings.extend(warnings)

                if warnings and strict:
                    warning_msg = "Agent specs have warnings (strict mode):\n"
                    for warning in warnings:
                        warning_msg += f"  - {warning}\n"
                    raise ValueError(warning_msg)

            except ImportError:
                # Formatter/validator not available - continue with warning
                self._preparation_warnings.append(
                    "Agent spec formatting skipped (formatter not available)"
                )

        self._workspace_prepared = True

    def generate(
        self, ide: str, skip_format: bool = False, strict: bool = False
    ) -> str:
        """Generate IDE configuration content.

        Args:
            ide: Target IDE name
            skip_format: Skip formatting (only validate)
            strict: Treat warnings as errors

        Returns:
            Generated configuration content

        Raises:
            ValueError: If IDE is not supported or workspace invalid
            FileNotFoundError: If template is not found
        """
        config = self.get_ide_config(ide)
        if not config:
            raise ValueError(
                f"Unsupported IDE: {ide}. "
                f"Supported: {', '.join(self.get_supported_ides())}"
            )

        # Validate and format workspace before generation
        self._prepare_workspace(skip_format=skip_format, strict=strict)

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

    def generate_to_file(
        self,
        ide: str,
        output_dir: Path | None = None,
        skip_format: bool = False,
        strict: bool = False,
    ) -> Path:
        """Generate IDE config and write to file.

        Args:
            ide: Target IDE name
            output_dir: Output directory (defaults to .parac/integrations/ide/)
            skip_format: Skip formatting (only validate)
            strict: Treat warnings as errors

        Returns:
            Path to generated file
        """
        config = self.get_ide_config(ide)
        if not config:
            raise ValueError(f"Unsupported IDE: {ide}")

        # Generate content
        content = self.generate(ide, skip_format=skip_format, strict=strict)

        # Determine output path
        if output_dir is None:
            output_dir = self.ide_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / config.file_name
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_all(
        self,
        output_dir: Path | None = None,
        skip_format: bool = False,
        strict: bool = False,
    ) -> dict[str, Path]:
        """Generate configs for all supported IDEs.

        Args:
            output_dir: Output directory (defaults to .parac/integrations/ide/)
            skip_format: Skip formatting (only validate)
            strict: Treat warnings as errors

        Returns:
            Dictionary mapping IDE name to generated file path
        """
        # Prepare workspace once for all IDEs
        self._prepare_workspace(skip_format=skip_format, strict=strict)

        results = {}
        for ide in self.SUPPORTED_IDES:
            try:
                path = self.generate_to_file(
                    ide, output_dir, skip_format=True, strict=False
                )
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
            project_file = self.project_root / config.destination_dir / config.file_name

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

    # =========================================================================
    # MCP CONFIGURATION METHODS
    # =========================================================================

    def get_supported_mcp_ides(self) -> list[str]:
        """Get list of IDE names that support MCP configuration."""
        return list(self.SUPPORTED_MCP.keys())

    def get_mcp_config(self, ide: str) -> MCPConfig | None:
        """Get MCP configuration for a specific IDE."""
        return self.SUPPORTED_MCP.get(ide.lower())

    def generate_mcp_server_config(
        self,
        use_uv: bool = True,
        use_npx: bool = False,
    ) -> dict[str, Any]:
        """Generate the Paracle MCP server configuration.

        Args:
            use_uv: Use uv to run paracle (recommended)
            use_npx: Use npx instead (for npm-based installs)

        Returns:
            Dictionary with MCP server configuration
        """
        if use_uv:
            return {
                "paracle": {
                    "type": "stdio",
                    "command": "uv",
                    "args": ["run", "paracle", "mcp", "serve", "--stdio"],
                }
            }
        elif use_npx:
            return {
                "paracle": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["-y", "paracle", "mcp", "serve", "--stdio"],
                }
            }
        else:
            return {
                "paracle": {
                    "type": "stdio",
                    "command": "paracle",
                    "args": ["mcp", "serve", "--stdio"],
                }
            }

    def generate_mcp_config_content(
        self,
        ide: str,
        use_uv: bool = True,
        include_comment: bool = True,
    ) -> str:
        """Generate MCP configuration JSON content for an IDE.

        Args:
            ide: Target IDE name
            use_uv: Use uv to run paracle
            include_comment: Include header comment

        Returns:
            JSON string with MCP configuration
        """
        import json

        config = self.get_mcp_config(ide)
        if not config:
            raise ValueError(
                f"Unsupported MCP IDE: {ide}. "
                f"Supported: {', '.join(self.get_supported_mcp_ides())}"
            )

        # Build MCP config
        server_config = self.generate_mcp_server_config(use_uv=use_uv)

        # Different IDEs have different top-level structure
        if ide in ("vscode", "cursor", "cline", "zed"):
            # VS Code style: { "servers": { ... } }
            mcp_config = {"servers": server_config}
        else:
            # Claude Desktop / Windsurf style: { "mcpServers": { ... } }
            mcp_config = {"mcpServers": server_config}

        # Convert to JSON
        json_content = json.dumps(mcp_config, indent=2)

        if include_comment:
            header = f"""// Paracle MCP Configuration for {config.display_name}
// Auto-generated - regenerate with: paracle ide mcp --generate
// Documentation: https://modelcontextprotocol.io/
//
// This connects your IDE to the Paracle MCP server for:
// - Agent execution tools
// - Workflow management
// - .parac/ governance tools
// - Memory and context tools
"""
            # JSON doesn't support comments, but most IDEs tolerate them
            # For strict JSON parsers, we'll put it in a separate file
            return header + json_content

        return json_content

    def generate_mcp_to_file(
        self,
        ide: str,
        output_dir: Path | None = None,
        use_uv: bool = True,
    ) -> Path:
        """Generate MCP config and write to file.

        Args:
            ide: Target IDE name
            output_dir: Output directory (defaults to .parac/integrations/mcp/)
            use_uv: Use uv to run paracle

        Returns:
            Path to generated file
        """
        config = self.get_mcp_config(ide)
        if not config:
            raise ValueError(f"Unsupported MCP IDE: {ide}")

        # Generate content (without comments for valid JSON)
        content = self.generate_mcp_config_content(
            ide, use_uv=use_uv, include_comment=False
        )

        # Determine output path
        if output_dir is None:
            output_dir = self.parac_root / "integrations" / "mcp"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{ide}_{config.file_name}"
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def generate_all_mcp(self, output_dir: Path | None = None) -> dict[str, Path]:
        """Generate MCP configs for all supported IDEs.

        Args:
            output_dir: Output directory

        Returns:
            Dictionary mapping IDE name to generated file path
        """
        results = {}
        for ide in self.SUPPORTED_MCP:
            try:
                path = self.generate_mcp_to_file(ide, output_dir)
                results[ide] = path
            except Exception as e:
                print(f"Warning: Failed to generate MCP config for {ide}: {e}")

        return results

    def copy_mcp_to_project(self, ide: str) -> Path:
        """Copy MCP config to the IDE's expected location.

        Args:
            ide: Target IDE name

        Returns:
            Path to copied file
        """
        config = self.get_mcp_config(ide)
        if not config:
            raise ValueError(f"Unsupported MCP IDE: {ide}")

        # Source file
        source_dir = self.parac_root / "integrations" / "mcp"
        source = source_dir / f"{ide}_{config.file_name}"
        if not source.exists():
            self.generate_mcp_to_file(ide)
            source = source_dir / f"{ide}_{config.file_name}"

        # Destination
        if config.uses_home_dir:
            dest_dir = Path.home() / config.destination_dir
        else:
            dest_dir = self.project_root / config.destination_dir

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / config.file_name

        # Copy content
        content = source.read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")

        return dest

    def copy_all_mcp_to_project(self, project_only: bool = True) -> dict[str, Path]:
        """Copy all MCP configs to their expected locations.

        Args:
            project_only: If True, skip configs that go to home directory

        Returns:
            Dictionary mapping IDE name to copied file path
        """
        results = {}
        for ide, config in self.SUPPORTED_MCP.items():
            if project_only and config.uses_home_dir:
                continue
            try:
                path = self.copy_mcp_to_project(ide)
                results[ide] = path
            except Exception as e:
                print(f"Warning: Failed to copy MCP config for {ide}: {e}")

        return results

    def get_mcp_status(self) -> dict[str, Any]:
        """Get status of MCP configurations.

        Returns:
            Dictionary with MCP status information
        """
        status = {
            "supported_ides": self.get_supported_mcp_ides(),
            "configs": {},
        }

        mcp_dir = self.parac_root / "integrations" / "mcp"

        for ide, config in self.SUPPORTED_MCP.items():
            generated_file = mcp_dir / f"{ide}_{config.file_name}"

            if config.uses_home_dir:
                installed_file = Path.home() / config.destination_dir / config.file_name
            else:
                installed_file = (
                    self.project_root / config.destination_dir / config.file_name
                )

            status["configs"][ide] = {
                "display_name": config.display_name,
                "generated": generated_file.exists(),
                "installed": installed_file.exists(),
                "generated_path": (
                    str(generated_file) if generated_file.exists() else None
                ),
                "installed_path": (
                    str(installed_file) if installed_file.exists() else None
                ),
                "uses_home_dir": config.uses_home_dir,
            }

        return status
