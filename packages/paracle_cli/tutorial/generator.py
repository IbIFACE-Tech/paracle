"""Tutorial content generator from CLI metadata.

Generates tutorial content, examples, and documentation
automatically from Click command introspection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paracle_cli.tutorial.introspector import CommandInfo, ParameterInfo


@dataclass
class TutorialStep:
    """A single step in a generated tutorial."""

    title: str
    description: str
    action: str = ""  # What user should do
    example: str = ""  # Example command or code
    tips: list[str] = field(default_factory=list)
    validation: str = ""  # How to verify step completed


@dataclass
class GeneratedTutorial:
    """A generated tutorial for a command."""

    command_path: str
    title: str
    overview: str
    prerequisites: list[str] = field(default_factory=list)
    steps: list[TutorialStep] = field(default_factory=list)
    common_patterns: list[str] = field(default_factory=list)
    related_commands: list[str] = field(default_factory=list)
    troubleshooting: list[tuple[str, str]] = field(default_factory=list)


class TutorialGenerator:
    """Generates tutorials from command metadata."""

    def __init__(self):
        """Initialize tutorial generator."""
        # Templates for different command patterns
        self._templates: dict[str, str] = {}

    def generate(self, command: CommandInfo) -> GeneratedTutorial:
        """Generate a complete tutorial for a command.

        Args:
            command: CommandInfo from introspector.

        Returns:
            GeneratedTutorial with all sections.
        """
        tutorial = GeneratedTutorial(
            command_path=command.path,
            title=self._generate_title(command),
            overview=self._generate_overview(command),
        )

        # Generate prerequisites
        tutorial.prerequisites = self._generate_prerequisites(command)

        # Generate steps
        tutorial.steps = self._generate_steps(command)

        # Generate common patterns
        tutorial.common_patterns = self._generate_patterns(command)

        # Generate related commands
        tutorial.related_commands = self._generate_related(command)

        # Generate troubleshooting
        tutorial.troubleshooting = self._generate_troubleshooting(command)

        return tutorial

    def _generate_title(self, command: CommandInfo) -> str:
        """Generate tutorial title."""
        parts = command.path.split("/")
        action = parts[-1].replace("-", " ").title()
        if len(parts) > 1:
            context = parts[-2].replace("-", " ").title()
            return f"{context}: {action}"
        return action

    def _generate_overview(self, command: CommandInfo) -> str:
        """Generate overview section."""
        if command.help_text:
            # Clean up help text
            overview = command.help_text.strip()
            # Remove "Examples:" section if present
            if "Examples:" in overview:
                overview = overview.split("Examples:")[0].strip()
            return overview

        # Generate from command name
        action = command.name.replace("-", " ")
        if command.is_group:
            return f"Commands for {action} management."
        return f"Performs {action} operation."

    def _generate_prerequisites(self, command: CommandInfo) -> list[str]:
        """Generate prerequisites list."""
        prereqs = []

        # Check if command is in agents group
        if command.path.startswith("agents"):
            prereqs.append("Initialized .parac/ workspace (run `paracle init`)")
            prereqs.append("At least one agent spec in .parac/agents/specs/")

        # Check if command is in workflow group
        if command.path.startswith("workflow"):
            prereqs.append("Initialized .parac/ workspace (run `paracle init`)")
            prereqs.append("At least one workflow in .parac/workflows/")

        # Check for API key requirements
        api_related = ["run", "execute", "chat", "test"]
        if any(word in command.name for word in api_related):
            prereqs.append("API key configured (see `paracle config api-keys`)")

        return prereqs

    def _generate_steps(self, command: CommandInfo) -> list[TutorialStep]:
        """Generate tutorial steps."""
        steps = []

        # Step 1: Understanding the command
        steps.append(
            TutorialStep(
                title="Understanding the Command",
                description=command.help_text or f"The `{command.name}` command.",
                action="Review what this command does",
                example=f"paracle {command.path.replace('/', ' ')} --help",
                tips=["Use --help on any command to see available options"],
            )
        )

        # Step 2: Required parameters (if any)
        if command.required_args or command.required_options:
            step = self._generate_required_params_step(command)
            steps.append(step)

        # Step 3: Optional parameters (if any)
        if command.optional_options:
            step = self._generate_optional_params_step(command)
            steps.append(step)

        # Step 4: Flags (if any)
        if command.flags:
            step = self._generate_flags_step(command)
            steps.append(step)

        # Step 5: Running the command
        steps.append(
            TutorialStep(
                title="Running the Command",
                description="Execute the command with your parameters.",
                action="Run the command",
                example=command.build_example_command(),
                tips=self._generate_execution_tips(command),
            )
        )

        # Step 6: For groups, show subcommands
        if command.is_group and command.subcommands:
            step = self._generate_subcommands_step(command)
            steps.append(step)

        return steps

    def _generate_required_params_step(
        self,
        command: CommandInfo,
    ) -> TutorialStep:
        """Generate step for required parameters."""
        params: list[ParameterInfo] = []
        params.extend(command.required_args)
        params.extend(command.required_options)

        param_descriptions = []
        for p in params:
            desc = f"- **{p.display_name}**"
            if p.help_text:
                desc += f": {p.help_text}"
            if p.choices:
                desc += f" (choices: {', '.join(p.choices)})"
            param_descriptions.append(desc)

        return TutorialStep(
            title="Required Parameters",
            description="These parameters must be provided:\n\n"
            + "\n".join(param_descriptions),
            action="Prepare your required values",
            example=self._build_params_example(params),
            tips=[f"Required: {p.display_name}" for p in params[:3]],
        )

    def _generate_optional_params_step(
        self,
        command: CommandInfo,
    ) -> TutorialStep:
        """Generate step for optional parameters."""
        params = command.optional_options

        param_descriptions = []
        for p in params:
            desc = f"- **{p.opts[-1] if p.opts else p.name}**"
            if p.help_text:
                desc += f": {p.help_text}"
            if p.default and p.default != ():
                desc += f" (default: {p.default})"
            param_descriptions.append(desc)

        return TutorialStep(
            title="Optional Parameters",
            description="These parameters are optional:\n\n"
            + "\n".join(param_descriptions[:5]),  # Limit to 5
            action="Add optional parameters as needed",
            tips=[
                "Optional parameters have sensible defaults",
                "Use them to customize behavior",
            ],
        )

    def _generate_flags_step(self, command: CommandInfo) -> TutorialStep:
        """Generate step for flag options."""
        flags = command.flags

        flag_descriptions = []
        for f in flags:
            desc = f"- **{f.opts[-1] if f.opts else f.name}**"
            if f.help_text:
                desc += f": {f.help_text}"
            flag_descriptions.append(desc)

        return TutorialStep(
            title="Flags",
            description="Available flags (on/off switches):\n\n"
            + "\n".join(flag_descriptions[:5]),
            action="Add flags to modify behavior",
            tips=[
                "Flags don't take values, just add them to enable",
            ],
        )

    def _generate_subcommands_step(self, command: CommandInfo) -> TutorialStep:
        """Generate step for subcommands."""
        subcmd_list = []
        for sub in command.subcommands[:8]:  # Limit to 8
            desc = f"- **{sub.name}**"
            if sub.short_help:
                desc += f": {sub.short_help}"
            elif sub.help_text:
                first_line = sub.help_text.split("\n")[0]
                desc += f": {first_line[:60]}..."
            subcmd_list.append(desc)

        return TutorialStep(
            title="Available Subcommands",
            description="This command group has these subcommands:\n\n"
            + "\n".join(subcmd_list),
            action="Choose a subcommand to run",
            example=f"paracle {command.path.replace('/', ' ')} <subcommand>",
            tips=[
                "Use --help on subcommands for more details",
                "Run `paracle tutorial learn <subcommand>` for tutorials",
            ],
        )

    def _generate_execution_tips(self, command: CommandInfo) -> list[str]:
        """Generate tips for command execution."""
        tips = []

        # Check for common options
        option_names = [o.name for o in command.options]

        if "verbose" in option_names or any("-v" in o.opts for o in command.options):
            tips.append("Use -v or --verbose for detailed output")

        if "json" in option_names or "format" in option_names:
            tips.append("Use --json or --format=json for machine-readable output")

        if "dry_run" in option_names or "dry-run" in option_names:
            tips.append("Use --dry-run to preview changes without applying")

        if "force" in option_names:
            tips.append("Use --force to override safety checks (use carefully!)")

        if not tips:
            tips.append("Check the output for success or error messages")

        return tips

    def _build_params_example(self, params: list[ParameterInfo]) -> str:
        """Build example showing parameter usage."""
        lines = []
        for p in params:
            if p.param_type == "argument":
                lines.append(f"# {p.name}: {p.example_value}")
            else:
                flag = p.opts[-1] if p.opts else f"--{p.name}"
                lines.append(f"{flag} {p.example_value}")
        return "\n".join(lines)

    def _generate_patterns(self, command: CommandInfo) -> list[str]:
        """Generate common usage patterns."""
        patterns = []

        # Basic usage
        patterns.append(f"Basic: `paracle {command.path.replace('/', ' ')}`")

        # With required params
        if command.required_args or command.required_options:
            patterns.append(
                f"With required params: `{command.build_example_command()}`"
            )

        # Common flag combinations
        flag_names = [f.name for f in command.flags]
        if "verbose" in flag_names:
            patterns.append(
                f"Verbose mode: `paracle {command.path.replace('/', ' ')} -v`"
            )
        if "json" in [o.name for o in command.options]:
            patterns.append(
                f"JSON output: `paracle {command.path.replace('/', ' ')} --json`"
            )

        return patterns

    def _generate_related(self, command: CommandInfo) -> list[str]:
        """Generate related commands list."""
        related = []

        # Sibling commands (same parent)
        if command.parent:
            for sibling in command.parent.subcommands:
                if sibling.name != command.name and not sibling.hidden:
                    related.append(f"paracle {sibling.path.replace('/', ' ')}")

        # Parent group
        if command.parent and command.parent.path:
            related.append(f"paracle {command.parent.path.replace('/', ' ')} --help")

        return related[:5]  # Limit to 5

    def _generate_troubleshooting(
        self,
        command: CommandInfo,
    ) -> list[tuple[str, str]]:
        """Generate troubleshooting tips."""
        tips = []

        # Common issues based on command type
        if command.path.startswith("agents"):
            tips.append(
                (
                    "Agent not found",
                    "Ensure .parac/agents/specs/<agent>.md exists and is valid",
                )
            )
            tips.append(
                (
                    "Validation errors",
                    "Run `paracle agents format` to auto-fix common issues",
                )
            )

        if command.path.startswith("workflow"):
            tips.append(
                ("Workflow not found", "Check that .parac/workflows/<name>.yaml exists")
            )

        # API-related commands
        api_words = ["run", "execute", "chat"]
        if any(word in command.name for word in api_words):
            tips.append(
                ("API key errors", "Ensure your .env file contains valid API keys")
            )

        # General tips
        tips.append(
            ("Permission denied", "Check file permissions in .parac/ directory")
        )

        return tips

    def format_as_markdown(self, tutorial: GeneratedTutorial) -> str:
        """Format tutorial as markdown.

        Args:
            tutorial: Generated tutorial.

        Returns:
            Markdown string.
        """
        lines = []

        # Title
        lines.append(f"# {tutorial.title}")
        lines.append("")

        # Overview
        lines.append("## Overview")
        lines.append("")
        lines.append(tutorial.overview)
        lines.append("")

        # Prerequisites
        if tutorial.prerequisites:
            lines.append("## Prerequisites")
            lines.append("")
            for prereq in tutorial.prerequisites:
                lines.append(f"- {prereq}")
            lines.append("")

        # Steps
        lines.append("## Steps")
        lines.append("")
        for i, step in enumerate(tutorial.steps, 1):
            lines.append(f"### Step {i}: {step.title}")
            lines.append("")
            lines.append(step.description)
            lines.append("")
            if step.example:
                lines.append("```bash")
                lines.append(step.example)
                lines.append("```")
                lines.append("")
            if step.tips:
                lines.append("**Tips:**")
                for tip in step.tips:
                    lines.append(f"- {tip}")
                lines.append("")

        # Common patterns
        if tutorial.common_patterns:
            lines.append("## Common Patterns")
            lines.append("")
            for pattern in tutorial.common_patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        # Related commands
        if tutorial.related_commands:
            lines.append("## Related Commands")
            lines.append("")
            for cmd in tutorial.related_commands:
                lines.append(f"- `{cmd}`")
            lines.append("")

        # Troubleshooting
        if tutorial.troubleshooting:
            lines.append("## Troubleshooting")
            lines.append("")
            for problem, solution in tutorial.troubleshooting:
                lines.append(f"**{problem}**")
                lines.append(f": {solution}")
                lines.append("")

        return "\n".join(lines)
