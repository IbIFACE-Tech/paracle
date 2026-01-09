"""CLI introspector for extracting command metadata.

Provides tools to introspect Click commands and extract metadata
for automatic tutorial generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import click


@dataclass
class ParameterInfo:
    """Information about a CLI parameter (option or argument)."""

    name: str
    param_type: str  # "option" or "argument"
    click_type: str  # STRING, INT, Choice, etc.
    required: bool = False
    default: Any = None
    help_text: str = ""
    opts: list[str] = field(default_factory=list)  # ['-t', '--task']
    is_flag: bool = False
    multiple: bool = False
    choices: list[str] = field(default_factory=list)
    envvar: str | None = None

    @property
    def display_name(self) -> str:
        """Get display name for prompts."""
        if self.opts:
            return self.opts[-1].lstrip("-")
        return self.name

    @property
    def example_value(self) -> str:
        """Generate example value based on type."""
        if self.choices:
            return self.choices[0]
        if self.default and self.default != ():
            return str(self.default)

        type_examples = {
            "STRING": '"example"',
            "INT": "42",
            "FLOAT": "3.14",
            "BOOL": "true",
            "PATH": "./path/to/file",
            "FILE": "./file.txt",
            "DIRECTORY": "./directory",
            "UUID": "123e4567-e89b-12d3-a456-426614174000",
        }
        return type_examples.get(self.click_type, "<value>")


@dataclass
class CommandInfo:
    """Information about a CLI command."""

    name: str
    path: str  # Full path like "agents/run"
    help_text: str = ""
    short_help: str = ""
    is_group: bool = False
    arguments: list[ParameterInfo] = field(default_factory=list)
    options: list[ParameterInfo] = field(default_factory=list)
    subcommands: list[CommandInfo] = field(default_factory=list)
    parent: CommandInfo | None = None
    deprecated: bool = False
    hidden: bool = False

    @property
    def required_args(self) -> list[ParameterInfo]:
        """Get required arguments."""
        return [a for a in self.arguments if a.required]

    @property
    def required_options(self) -> list[ParameterInfo]:
        """Get required options."""
        return [o for o in self.options if o.required]

    @property
    def optional_options(self) -> list[ParameterInfo]:
        """Get optional (non-flag) options."""
        return [o for o in self.options if not o.required and not o.is_flag]

    @property
    def flags(self) -> list[ParameterInfo]:
        """Get flag options."""
        return [o for o in self.options if o.is_flag]

    def build_example_command(self, with_optionals: bool = False) -> str:
        """Build an example command string."""
        parts = [f"paracle {self.path.replace('/', ' ')}"]

        # Add required arguments
        for arg in self.required_args:
            parts.append(f"<{arg.name}>")

        # Add required options
        for opt in self.required_options:
            flag = opt.opts[-1] if opt.opts else f"--{opt.name}"
            parts.append(f"{flag} {opt.example_value}")

        # Add optional ones if requested
        if with_optionals:
            for opt in self.optional_options[:2]:  # Limit to 2
                flag = opt.opts[-1] if opt.opts else f"--{opt.name}"
                parts.append(f"[{flag} {opt.example_value}]")

        return " ".join(parts)


class CLIIntrospector:
    """Introspects Click CLI commands to extract metadata."""

    def __init__(self, root_command: click.BaseCommand):
        """Initialize with root CLI command.

        Args:
            root_command: The root Click command (usually the main group).
        """
        self.root = root_command
        self._cache: dict[str, CommandInfo] = {}
        self._root_name = root_command.name or "cli"

    def get_all_commands(self) -> dict[str, CommandInfo]:
        """Get all commands as a flat dictionary.

        Returns:
            Dictionary mapping command paths to CommandInfo.
            Paths are relative (without root name prefix).
        """
        if not self._cache:
            # Build cache starting from subcommands of root
            if isinstance(self.root, click.Group):
                for subcmd in self.root.commands.values():
                    self._build_cache(subcmd, "")
        return self._cache

    def get_command(self, path: str) -> CommandInfo | None:
        """Get command info by path.

        Args:
            path: Command path like "agents" or "agents/run".

        Returns:
            CommandInfo or None if not found.
        """
        commands = self.get_all_commands()
        return commands.get(path)

    def find_command(self, query: str) -> list[CommandInfo]:
        """Find commands matching a query.

        Args:
            query: Search query (partial match on name or path).

        Returns:
            List of matching CommandInfo objects.
        """
        query_lower = query.lower()
        commands = self.get_all_commands()

        results = []
        for path, info in commands.items():
            if (
                query_lower in path.lower()
                or query_lower in info.name.lower()
                or (info.help_text and query_lower in info.help_text.lower())
            ):
                results.append(info)

        return results

    def get_command_tree(self) -> CommandInfo:
        """Get full command tree starting from root.

        Returns:
            Root CommandInfo with nested subcommands (paths without root prefix).
        """
        # Create a virtual root that represents "paracle"
        root_info = CommandInfo(
            name="paracle",
            path="",
            help_text=self.root.help or "",
            short_help=getattr(self.root, "short_help", "") or "",
            is_group=True,
        )

        # Add subcommands with paths starting from empty string
        if isinstance(self.root, click.Group):
            for subcmd in self.root.commands.values():
                child_info = self._extract_command_info(subcmd, "")
                child_info.parent = root_info
                root_info.subcommands.append(child_info)

        return root_info

    def resolve_command_path(self, path_parts: list[str]) -> CommandInfo | None:
        """Resolve a command from path parts.

        Args:
            path_parts: List of command parts like ["agents", "run"].

        Returns:
            CommandInfo or None if not found.
        """
        path = "/".join(path_parts)
        return self.get_command(path)

    def _build_cache(
        self,
        command: click.BaseCommand,
        parent_path: str,
    ) -> None:
        """Build the command cache recursively."""
        info = self._extract_command_info(command, parent_path)
        self._cache[info.path] = info

        if isinstance(command, click.Group):
            for subcmd in command.commands.values():
                self._build_cache(subcmd, info.path)

    def _extract_command_info(
        self,
        command: click.BaseCommand,
        parent_path: str,
    ) -> CommandInfo:
        """Extract metadata from a Click command."""
        name = command.name or ""
        path = f"{parent_path}/{name}" if parent_path else name

        info = CommandInfo(
            name=name,
            path=path,
            help_text=command.help or "",
            short_help=getattr(command, "short_help", "") or "",
            is_group=isinstance(command, click.Group),
            deprecated=getattr(command, "deprecated", False),
            hidden=getattr(command, "hidden", False),
        )

        # Extract parameters
        for param in command.params:
            param_info = self._extract_param_info(param)
            if param_info.param_type == "argument":
                info.arguments.append(param_info)
            else:
                info.options.append(param_info)

        # Extract subcommands for groups
        if isinstance(command, click.Group):
            for subcmd in command.commands.values():
                child_info = self._extract_command_info(subcmd, path)
                child_info.parent = info
                info.subcommands.append(child_info)

        return info

    def _extract_param_info(self, param: click.Parameter) -> ParameterInfo:
        """Extract metadata from a Click parameter."""
        is_option = isinstance(param, click.Option)

        # Get type name
        type_name = "STRING"
        if param.type:
            if isinstance(param.type, click.Choice):
                type_name = "CHOICE"
            elif isinstance(param.type, click.Path):
                type_name = "PATH"
            elif isinstance(param.type, click.File):
                type_name = "FILE"
            elif hasattr(param.type, "name"):
                type_name = param.type.name.upper()

        # Get choices if Choice type
        choices: list[str] = []
        if isinstance(param.type, click.Choice):
            choices = list(param.type.choices)

        return ParameterInfo(
            name=param.name or "",
            param_type="option" if is_option else "argument",
            click_type=type_name,
            required=param.required,
            default=param.default,
            help_text=getattr(param, "help", "") or "",
            opts=list(getattr(param, "opts", [])),
            is_flag=getattr(param, "is_flag", False),
            multiple=param.multiple,
            choices=choices,
            envvar=getattr(param, "envvar", None),
        )

    def list_all_paths(self) -> list[str]:
        """Get list of all command paths.

        Returns:
            Sorted list of command paths.
        """
        commands = self.get_all_commands()
        return sorted(commands.keys())

    def get_commands_with_option(self, option_name: str) -> list[CommandInfo]:
        """Find all commands that have a specific option.

        Args:
            option_name: Option name (with or without dashes).

        Returns:
            List of commands with that option.
        """
        # Normalize option name
        if not option_name.startswith("-"):
            option_name = f"--{option_name}"

        results = []
        for info in self.get_all_commands().values():
            for opt in info.options:
                if option_name in opt.opts:
                    results.append(info)
                    break

        return results
