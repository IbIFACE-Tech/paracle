"""Interactive tutorial runner.

Provides an interactive experience for learning CLI commands,
with prompts, validation, and real-time execution.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

if TYPE_CHECKING:
    from paracle_cli.tutorial.generator import GeneratedTutorial, TutorialStep
    from paracle_cli.tutorial.introspector import CommandInfo, ParameterInfo


console = Console()


@dataclass
class CollectedParameter:
    """A parameter value collected from user."""

    name: str
    value: Any
    param_type: str  # "argument" or "option"
    opts: list[str] = field(default_factory=list)
    is_flag: bool = False


class InteractiveTutorialRunner:
    """Runs interactive tutorials for CLI commands."""

    def __init__(self, dry_run: bool = False):
        """Initialize runner.

        Args:
            dry_run: If True, show commands but don't execute.
        """
        self.dry_run = dry_run
        self.collected_params: list[CollectedParameter] = []

    def run_tutorial(
        self,
        command: CommandInfo,
        tutorial: GeneratedTutorial,
    ) -> bool:
        """Run an interactive tutorial for a command.

        Args:
            command: The command metadata.
            tutorial: Generated tutorial content.

        Returns:
            True if completed successfully.
        """
        self._show_header(command, tutorial)

        # Show prerequisites
        if tutorial.prerequisites:
            if not self._check_prerequisites(tutorial.prerequisites):
                return False

        # Run through steps interactively
        for i, step in enumerate(tutorial.steps, 1):
            console.print()
            if not self._run_step(i, len(tutorial.steps), step, command):
                console.print(
                    "\n[yellow]Tutorial paused. " "Run again to continue.[/yellow]"
                )
                return False

        # Show completion and related commands
        self._show_completion(command, tutorial)
        return True

    def run_quick_guide(self, command: CommandInfo) -> None:
        """Run a quick non-interactive guide.

        Args:
            command: The command metadata.
        """
        console.print(
            Panel(
                f"[bold cyan]Quick Guide: {command.path}[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print()

        # Show help text
        if command.help_text:
            console.print("[bold]Description:[/bold]")
            console.print(command.help_text.strip())
            console.print()

        # Show usage
        console.print("[bold]Usage:[/bold]")
        console.print(f"  paracle {command.path.replace('/', ' ')} [OPTIONS]")
        console.print()

        # Show required params
        if command.required_args or command.required_options:
            console.print("[bold]Required:[/bold]")
            for arg in command.required_args:
                console.print(f"  {arg.name} ({arg.click_type})")
            for opt in command.required_options:
                flags = ", ".join(opt.opts) if opt.opts else f"--{opt.name}"
                console.print(f"  {flags}: {opt.help_text}")
            console.print()

        # Show optional params
        if command.optional_options:
            console.print("[bold]Options:[/bold]")
            for opt in command.optional_options[:5]:
                flags = ", ".join(opt.opts) if opt.opts else f"--{opt.name}"
                default = f" (default: {opt.default})" if opt.default else ""
                console.print(f"  {flags}: {opt.help_text}{default}")
            if len(command.optional_options) > 5:
                console.print(f"  ... and {len(command.optional_options) - 5} more")
            console.print()

        # Show flags
        if command.flags:
            console.print("[bold]Flags:[/bold]")
            for flag in command.flags[:5]:
                flags = ", ".join(flag.opts) if flag.opts else f"--{flag.name}"
                console.print(f"  {flags}: {flag.help_text}")
            console.print()

        # Show example
        console.print("[bold]Example:[/bold]")
        console.print(f"  {command.build_example_command()}")
        console.print()

        # Show subcommands for groups
        if command.is_group and command.subcommands:
            console.print("[bold]Subcommands:[/bold]")
            table = Table(show_header=False, box=None)
            table.add_column("Command", style="cyan")
            table.add_column("Description")
            for sub in command.subcommands[:10]:
                desc = sub.short_help or sub.help_text.split("\n")[0][:50]
                table.add_row(sub.name, desc)
            console.print(table)
            console.print()

    def collect_parameters_interactive(
        self,
        command: CommandInfo,
    ) -> list[CollectedParameter]:
        """Interactively collect parameter values from user.

        Args:
            command: The command to collect parameters for.

        Returns:
            List of collected parameters.
        """
        self.collected_params = []

        console.print(
            Panel(
                f"[bold cyan]Parameter Collection: {command.name}[/bold cyan]",
                border_style="cyan",
            )
        )
        console.print()

        # Collect required arguments
        for arg in command.required_args:
            value = self._prompt_for_param(arg, required=True)
            self.collected_params.append(
                CollectedParameter(
                    name=arg.name,
                    value=value,
                    param_type="argument",
                )
            )

        # Collect required options
        for opt in command.required_options:
            value = self._prompt_for_param(opt, required=True)
            self.collected_params.append(
                CollectedParameter(
                    name=opt.name,
                    value=value,
                    param_type="option",
                    opts=opt.opts,
                )
            )

        # Ask about optional parameters
        if command.optional_options:
            console.print()
            if Confirm.ask("Would you like to set optional parameters?", default=False):
                for opt in command.optional_options:
                    value = self._prompt_for_param(opt, required=False)
                    if value:
                        self.collected_params.append(
                            CollectedParameter(
                                name=opt.name,
                                value=value,
                                param_type="option",
                                opts=opt.opts,
                            )
                        )

        # Ask about flags
        if command.flags:
            console.print()
            console.print("[dim]Available flags:[/dim]")
            for flag in command.flags:
                flag_str = flag.opts[-1] if flag.opts else f"--{flag.name}"
                if Confirm.ask(f"  Enable {flag_str}?", default=False):
                    self.collected_params.append(
                        CollectedParameter(
                            name=flag.name,
                            value=True,
                            param_type="option",
                            opts=flag.opts,
                            is_flag=True,
                        )
                    )

        return self.collected_params

    def build_command(
        self,
        command: CommandInfo,
        params: list[CollectedParameter] | None = None,
    ) -> str:
        """Build the full command string from collected parameters.

        Args:
            command: The command metadata.
            params: Collected parameters (uses self.collected_params if None).

        Returns:
            Full command string.
        """
        params = params or self.collected_params
        parts = [f"paracle {command.path.replace('/', ' ')}"]

        # Add arguments first (positional)
        for p in params:
            if p.param_type == "argument":
                # Quote if contains spaces
                value = str(p.value)
                if " " in value:
                    value = f'"{value}"'
                parts.append(value)

        # Add options
        for p in params:
            if p.param_type == "option":
                flag = p.opts[-1] if p.opts else f"--{p.name}"
                if p.is_flag:
                    parts.append(flag)
                else:
                    value = str(p.value)
                    if " " in value:
                        value = f'"{value}"'
                    parts.append(f"{flag} {value}")

        return " ".join(parts)

    def execute_command(
        self,
        command_str: str,
        capture: bool = False,
    ) -> tuple[int, str, str]:
        """Execute a command.

        Args:
            command_str: Full command string.
            capture: Whether to capture output.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        if self.dry_run:
            console.print(f"\n[dim]Would execute: {command_str}[/dim]")
            return (0, "", "")

        console.print(f"\n[dim]Executing: {command_str}[/dim]")
        console.print()

        try:
            result = subprocess.run(
                command_str,
                shell=True,
                capture_output=capture,
                text=True,
                cwd=Path.cwd(),
            )
            return (
                result.returncode,
                result.stdout if capture else "",
                result.stderr if capture else "",
            )
        except Exception as e:
            return (1, "", str(e))

    def _show_header(
        self,
        command: CommandInfo,
        tutorial: GeneratedTutorial,
    ) -> None:
        """Show tutorial header."""
        console.print(
            Panel(
                f"[bold green]Interactive Tutorial: {tutorial.title}[/bold green]\n\n"
                f"{tutorial.overview[:200]}...",
                border_style="green",
            )
        )

    def _check_prerequisites(self, prerequisites: list[str]) -> bool:
        """Check and display prerequisites."""
        console.print("\n[bold]Prerequisites:[/bold]")
        for prereq in prerequisites:
            console.print(f"  - {prereq}")

        console.print()
        return Confirm.ask("Do you have these prerequisites ready?", default=True)

    def _run_step(
        self,
        step_num: int,
        total_steps: int,
        step: TutorialStep,
        command: CommandInfo,
    ) -> bool:
        """Run a single tutorial step.

        Returns:
            True to continue, False to pause.
        """
        # Show step header
        console.print(
            Panel(
                f"[bold cyan]Step {step_num}/{total_steps}: {step.title}[/bold cyan]",
                border_style="cyan",
            )
        )

        # Show description
        console.print()
        console.print(step.description)

        # Show example if present
        if step.example:
            console.print()
            console.print("[bold]Example:[/bold]")
            console.print(Syntax(step.example, "bash", theme="monokai"))

        # Show tips
        if step.tips:
            console.print()
            console.print("[bold]Tips:[/bold]")
            for tip in step.tips:
                console.print(f"  [dim]→ {tip}[/dim]")

        # Interactive prompt based on step type
        console.print()

        # For parameter steps, collect interactively
        if "Required Parameters" in step.title:
            if Confirm.ask("Would you like to enter values interactively?"):
                self._collect_required_params(command)

        # For execution step, offer to run
        if "Running" in step.title:
            return self._offer_execution(command)

        return Confirm.ask("Continue to next step?", default=True)

    def _collect_required_params(self, command: CommandInfo) -> None:
        """Collect required parameters."""
        for arg in command.required_args:
            self._prompt_for_param(arg, required=True)
        for opt in command.required_options:
            self._prompt_for_param(opt, required=True)

    def _prompt_for_param(
        self,
        param: ParameterInfo,
        required: bool,
    ) -> Any:
        """Prompt user for a parameter value."""
        # Build prompt text
        display = param.display_name
        if param.help_text:
            display = f"{display} ({param.help_text})"

        # Handle choices
        if param.choices:
            console.print(f"[cyan]Choose {param.name}:[/cyan]")
            for i, choice in enumerate(param.choices, 1):
                console.print(f"  {i}. {choice}")
            idx = Prompt.ask("Selection", default="1" if not required else None)
            try:
                return param.choices[int(idx) - 1]
            except (ValueError, IndexError):
                return param.choices[0]

        # Handle different types
        default = None
        if param.default and param.default != ():
            default = str(param.default)

        if param.click_type == "INT":
            value = Prompt.ask(display, default=default)
            return int(value) if value else None
        elif param.click_type == "FLOAT":
            value = Prompt.ask(display, default=default)
            return float(value) if value else None
        elif param.click_type in ("PATH", "FILE", "DIRECTORY"):
            value = Prompt.ask(f"{display} (path)", default=default)
            return value
        else:
            return Prompt.ask(display, default=default)

    def _offer_execution(self, command: CommandInfo) -> bool:
        """Offer to execute the command."""
        if self.collected_params:
            cmd_str = self.build_command(command)
            console.print("\n[bold]Command to execute:[/bold]")
            console.print(Syntax(cmd_str, "bash", theme="monokai"))
            console.print()

            choice = Prompt.ask(
                "What would you like to do?",
                choices=["run", "edit", "skip", "quit"],
                default="skip",
            )

            if choice == "run":
                return_code, _, _ = self.execute_command(cmd_str)
                if return_code == 0:
                    console.print("[green]Command executed successfully![/green]")
                else:
                    console.print(f"[red]Command failed (code {return_code})[/red]")
                return True
            elif choice == "edit":
                new_cmd = Prompt.ask("Edit command", default=cmd_str)
                return_code, _, _ = self.execute_command(new_cmd)
                return True
            elif choice == "quit":
                return False

        return True

    def _show_completion(
        self,
        command: CommandInfo,
        tutorial: GeneratedTutorial,
    ) -> None:
        """Show tutorial completion message."""
        console.print()
        console.print(
            Panel(
                f"[bold green]Tutorial Complete![/bold green]\n\n"
                f"You've learned how to use `paracle {command.path.replace('/', ' ')}`",
                border_style="green",
            )
        )

        # Show related commands
        if tutorial.related_commands:
            console.print("\n[bold]Related commands to explore:[/bold]")
            for cmd in tutorial.related_commands:
                console.print(f"  • {cmd}")

        # Show next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  • Run `paracle tutorial list` to see all commands")
        console.print("  • Run `paracle <command> --help` for detailed help")
        console.print("  • Run `paracle tutorial learn <command>` for more tutorials")
