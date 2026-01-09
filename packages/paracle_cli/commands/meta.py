"""CLI commands for paracle_meta AI engine.

Commands for managing the internal AI engine:
- skills: System-wide framework skills (meta-generation, meta-learning, etc.)
- generate: AI-powered artifact generation
- learn: Feedback and continuous improvement
- info: Engine information and status

This is separate from 'paracle agents' which manages user project agents.

Architecture:
- paracle agents: User agents in .parac/agents/ (project-level)
- paracle meta: Internal AI engine from paracle_meta package (system-level)
"""

from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom theme for chat - modern, clean aesthetic
_chat_theme = Theme(
    {
        "user": "bold cyan",
        "user.prompt": "cyan",
        "assistant": "bold green",
        "assistant.text": "white",
        "system": "bold yellow",
        "cost": "dim italic",
        "command": "bold magenta",
        "info": "dim",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "highlight": "bold white",
        "border": "bright_black",
    }
)

console = Console(theme=_chat_theme)

# Thinking messages for variety
_THINKING_MESSAGES = [
    "Thinking",
    "Processing",
    "Analyzing",
    "Considering",
    "Reflecting",
]


def _format_tokens(count: int) -> str:
    """Format token count with K/M suffixes."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def _get_thinking_message() -> str:
    """Get a random thinking message."""
    import random

    return random.choice(_THINKING_MESSAGES)


def _create_thinking_display() -> Text:
    """Create an animated thinking indicator."""
    text = Text()
    text.append("  ◇ ", style="dim green")
    text.append(_get_thinking_message(), style="dim italic")
    text.append("...", style="dim")
    return text


def _render_response(text: str, use_markdown: bool = True) -> None:
    """Render AI response with optional markdown formatting.

    Args:
        text: The response text to render.
        use_markdown: If True, render as markdown with syntax highlighting.
    """
    if not use_markdown:
        console.print(text)
        return

    try:
        # Render as markdown (handles code blocks, lists, headers, etc.)
        md = Markdown(text, code_theme="monokai")
        console.print(md)
    except Exception:
        # Fallback to plain text if markdown parsing fails
        console.print(text)


def get_system_skills_dir() -> Path:
    """Get the system skills directory (platform-specific)."""
    from paracle_core.paths import get_system_skills_dir as _get_system_skills_dir

    return _get_system_skills_dir()


@click.group()
def meta() -> None:
    """Paracle Meta AI Engine.

    Manage the internal AI-powered engine for artifact generation,
    learning, and advanced capabilities.

    This is separate from 'paracle agents' which manages user project agents.

    Commands:
        paracle meta info          - Show engine info
        paracle meta skills        - Manage system-wide skills
        paracle meta generate      - Generate artifacts with AI
        paracle meta learn         - Manage learning and feedback

    System skills are stored in platform-specific directories:
        Linux:   ~/.local/share/paracle/skills/
        macOS:   ~/Library/Application Support/Paracle/skills/
        Windows: %LOCALAPPDATA%\\Paracle\\skills\\
    """


@meta.command("info")
def meta_info() -> None:
    """Show paracle_meta engine information.

    Displays version, capabilities, and configuration status.
    """
    from paracle_core.paths import detect_platform, get_system_paths

    try:
        from paracle_meta import __version__ as meta_version
    except ImportError:
        meta_version = "not installed"

    platform = detect_platform()
    paths = get_system_paths()

    console.print(
        Panel(
            "[bold]Paracle Meta AI Engine[/bold]",
            title="paracle meta info",
        )
    )

    console.print(f"\n[bold]Version:[/bold] {meta_version}")
    console.print(f"[bold]Platform:[/bold] {platform}")
    console.print("\n[bold]System Directories:[/bold]")
    console.print(f"  Base:      {paths.base_dir}")
    console.print(f"  Skills:    {paths.skills_dir}")
    console.print(f"  Templates: {paths.templates_dir}")
    console.print(f"  Cache:     {paths.cache_dir}")

    # Check skills directory
    if paths.skills_dir.exists():
        skill_count = sum(
            1
            for d in paths.skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )
        console.print(f"\n[bold]System Skills:[/bold] {skill_count} installed")
    else:
        console.print("\n[bold]System Skills:[/bold] [yellow]Not initialized[/yellow]")
        console.print("  Run: paracle meta skills init")

    # Check providers
    console.print("\n[bold]Available Providers:[/bold]")
    providers = _check_providers()
    for name, available in providers.items():
        status = "[green]OK[/green]" if available else "[dim]not configured[/dim]"
        console.print(f"  {name}: {status}")

    console.print("\n[dim]Run 'paracle meta health' for detailed status[/dim]")


@meta.command("health")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--quick", is_flag=True, help="Quick check (database only)")
def meta_health(json_output: bool, quick: bool) -> None:
    """Check health of paracle_meta components.

    Performs comprehensive health checks:
    - Database connectivity
    - Provider availability
    - Learning engine status
    - Cost budget status

    Examples:
        paracle meta health           # Full health check
        paracle meta health --quick   # Quick database check
        paracle meta health --json    # JSON output for automation
    """
    import asyncio

    try:
        from paracle_meta.config import load_config
        from paracle_meta.database import MetaDatabase
        from paracle_meta.health import (
            HealthChecker,
            HealthStatus,
            format_health_report,
        )
    except ImportError:
        console.print("[red]Error:[/red] paracle_meta not installed")
        console.print("Install with: pip install paracle[meta]")
        raise SystemExit(1)

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not load config: {e}")
        config = None

    # Create database connection
    db = None
    try:
        if config:
            from paracle_meta.database import MetaDatabase

            db = MetaDatabase(config.database)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Could not connect to database: {e}")

    # Run health check
    checker = HealthChecker(config, db)

    try:
        if quick:
            status = asyncio.run(checker.quick_check())
            if json_output:
                console.print(f'{{"status": "{status.value}"}}')
            else:
                emoji = {"healthy": "[OK]", "degraded": "[!]", "unhealthy": "[X]"}[
                    status.value
                ]
                color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}[
                    status.value
                ]
                console.print(f"[{color}]{emoji} {status.value.upper()}[/{color}]")
            raise SystemExit(0 if status == HealthStatus.HEALTHY else 1)

        result = asyncio.run(checker.full_check())

        if json_output:
            console.print(result.model_dump_json(indent=2))
        else:
            report = format_health_report(result)
            console.print(report)

        # Exit code based on status
        if result.status == HealthStatus.HEALTHY:
            raise SystemExit(0)
        elif result.status == HealthStatus.DEGRADED:
            raise SystemExit(0)  # Degraded is still operational
        else:
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] Health check failed: {e}")
        raise SystemExit(1)
    finally:
        if db:
            db.disconnect()


def _check_providers() -> dict[str, bool]:
    """Check which AI providers are available."""
    import os

    return {
        "Anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
        "Google": bool(os.getenv("GOOGLE_API_KEY")),
        "Ollama": _check_ollama(),
    }


def _check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=1.0)
        return response.status_code == 200
    except Exception:
        return False


# =============================================================================
# Chat Mode (Enhanced with streaming, persistence, cost tracking)
# =============================================================================

# Cost tracking for chat sessions
_chat_costs: dict[str, dict] = {}


def _get_sessions_dir() -> Path:
    """Get sessions directory for persistence."""
    from paracle_core.paths import get_system_paths

    paths = get_system_paths()
    sessions_dir = paths.base_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def _load_session(session_id: str) -> tuple[list[dict[str, str]], dict]:
    """Load session from disk."""
    import json

    sessions_dir = _get_sessions_dir()
    session_file = sessions_dir / f"{session_id}.json"

    if session_file.exists():
        with open(session_file, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("messages", []), data.get("metadata", {})
    return [], {}


def _save_session(
    session_id: str,
    messages: list[dict[str, str]],
    metadata: dict,
) -> None:
    """Save session to disk."""
    import json

    sessions_dir = _get_sessions_dir()
    session_file = sessions_dir / f"{session_id}.json"

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "session_id": session_id,
                "messages": messages,
                "metadata": metadata,
                "updated_at": datetime.now().isoformat(),
            },
            f,
            indent=2,
        )


def _estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate cost for API call."""
    # Pricing per 1M tokens (approximate, as of 2024)
    pricing = {
        "anthropic": {
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
            "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
        },
        "openai": {
            "gpt-4o": {"input": 2.5, "output": 10.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        },
        "deepseek": {
            "deepseek-chat": {"input": 0.14, "output": 0.28},
            "deepseek-coder": {"input": 0.14, "output": 0.28},
            "deepseek-reasoner": {"input": 0.55, "output": 2.19},
        },
    }

    provider_pricing = pricing.get(provider.lower(), {})
    model_pricing = provider_pricing.get(model, {"input": 1.0, "output": 2.0})

    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost + output_cost


@meta.command("chat")
@click.option(
    "--provider",
    "-p",
    default="anthropic",
    help="AI provider (anthropic, openai, deepseek, ollama)",
)
@click.option("--model", "-m", help="Model to use (provider-specific)")
@click.option("--system", "-s", help="System prompt for the conversation")
@click.option("--session", help="Session ID to continue a previous chat")
@click.option(
    "--stream/--no-stream",
    default=True,
    help="Enable streaming output (default: enabled)",
)
@click.option(
    "--costs/--no-costs",
    default=True,
    help="Track and display costs (default: enabled)",
)
def meta_chat(
    provider: str,
    model: str | None,
    system: str | None,
    session: str | None,
    stream: bool,
    costs: bool,
) -> None:
    """Interactive chat with the Paracle Meta AI engine.

    Start an interactive conversation with AI for:
    - Generating Paracle artifacts (agents, workflows, skills)
    - Getting help with framework usage
    - Iterating on designs with follow-up questions

    Providers:
        anthropic  - Claude models (default)
        openai     - GPT models
        deepseek   - DeepSeek models (cost-effective)
        ollama     - Local models (free)

    Examples:
        paracle meta chat                          # Default (Anthropic)
        paracle meta chat -p openai                # Use OpenAI
        paracle meta chat -p deepseek              # Use DeepSeek (cheaper)
        paracle meta chat -p ollama -m llama3      # Use local Ollama
        paracle meta chat --session abc123         # Continue previous session
        paracle meta chat --no-stream              # Disable streaming

    Commands during chat:
        /exit, /quit, /q  - Exit chat
        /clear            - Clear conversation history
        /save <file>      - Save conversation to file
        /load <session>   - Load a previous session
        /sessions         - List saved sessions
        /cost             - Show session cost
        /help             - Show chat commands
    """
    import asyncio
    import uuid
    from datetime import datetime

    # Check provider availability
    providers_status = _check_providers()
    provider_map = {
        "anthropic": "Anthropic",
        "openai": "OpenAI",
        "deepseek": "DeepSeek",
        "ollama": "Ollama",
        "google": "Google",
    }

    provider_name = provider_map.get(provider.lower(), provider)

    # DeepSeek uses OpenAI-compatible API
    if provider.lower() == "deepseek":
        import os

        if not os.getenv("DEEPSEEK_API_KEY"):
            console.print("[red]Error:[/red] DeepSeek not configured")
            console.print("Set DEEPSEEK_API_KEY environment variable")
            raise SystemExit(1)
    elif provider_name in providers_status and not providers_status[provider_name]:
        if provider.lower() == "ollama":
            console.print("[red]Error:[/red] Ollama is not running")
            console.print("Start Ollama with: ollama serve")
        else:
            env_var = f"{provider.upper()}_API_KEY"
            console.print(f"[red]Error:[/red] {provider_name} not configured")
            console.print(f"Set {env_var} environment variable")
        raise SystemExit(1)

    # Default models per provider
    default_models = {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4o",
        "deepseek": "deepseek-chat",
        "ollama": "llama3",
        "google": "gemini-pro",
    }
    model = model or default_models.get(provider.lower(), "gpt-4o")

    # Session management
    session_id = session or str(uuid.uuid4())[:8]

    # Load existing session if provided
    messages: list[dict[str, str]] = []
    session_metadata: dict = {
        "provider": provider,
        "model": model,
        "created_at": datetime.now().isoformat(),
        "total_cost": 0.0,
        "total_tokens": {"input": 0, "output": 0},
    }

    if session:
        loaded_messages, loaded_metadata = _load_session(session)
        if loaded_messages:
            messages = loaded_messages
            session_metadata.update(loaded_metadata)
            console.print(
                f"[green]✓ Resumed session[/green] [dim]({len(messages)} messages)[/dim]"
            )

    # Initialize cost tracking
    _chat_costs[session_id] = {
        "total_cost": session_metadata.get("total_cost", 0.0),
        "total_tokens": session_metadata.get("total_tokens", {"input": 0, "output": 0}),
        "calls": 0,
    }

    # Welcome banner - elegant, modern design
    console.print()
    console.print(
        "[bold bright_cyan]  ╭──────────────────────────────────────────────────────────────╮[/bold bright_cyan]"
    )
    console.print(
        "[bold bright_cyan]  │[/bold bright_cyan]                                                              [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        "[bold bright_cyan]  │[/bold bright_cyan]   [bold white]◆ Paracle Chat[/bold white]                                             [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        "[bold bright_cyan]  │[/bold bright_cyan]                                                              [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        f"[bold bright_cyan]  │[/bold bright_cyan]   [dim]Provider[/dim]  [bold]{provider_name}[/bold]                                        [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        f"[bold bright_cyan]  │[/bold bright_cyan]   [dim]Model[/dim]     [bold]{model[:30]}[/bold]{'...' if len(model) > 30 else ''}                    [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        f"[bold bright_cyan]  │[/bold bright_cyan]   [dim]Session[/dim]   [bold]{session_id}[/bold]                                       [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        "[bold bright_cyan]  │[/bold bright_cyan]                                                              [bold bright_cyan]│[/bold bright_cyan]"
    )
    console.print(
        "[bold bright_cyan]  ╰──────────────────────────────────────────────────────────────╯[/bold bright_cyan]"
    )
    console.print()
    console.print("  [dim]💬 Type your message to start chatting[/dim]")
    console.print(
        "  [dim]📋 Commands:[/dim] [magenta]/help[/magenta] [dim]•[/dim] [magenta]/cost[/magenta] [dim]•[/dim] [magenta]/save[/magenta] [dim]•[/dim] [magenta]/exit[/magenta]"
    )
    console.print()

    # Default system prompt
    default_system = system or (
        "You are a helpful AI assistant for the Paracle multi-agent framework. "
        "You can help users design agents, workflows, skills, and policies. "
        "Provide clear, practical advice with code examples when appropriate."
    )

    async def chat_stream(user_message: str) -> str:
        """Get streaming chat completion."""
        if provider.lower() == "anthropic":
            return await _anthropic_stream(
                messages, user_message, model, default_system, session_id, costs
            )
        elif provider.lower() == "openai":
            return await _openai_stream(
                messages, user_message, model, default_system, session_id, costs
            )
        elif provider.lower() == "deepseek":
            return await _deepseek_stream(
                messages, user_message, model, default_system, session_id, costs
            )
        elif provider.lower() == "ollama":
            return await _ollama_stream(messages, user_message, model, default_system)
        else:
            return f"[Provider {provider} not yet implemented]"

    async def chat_completion(user_message: str) -> str:
        """Get non-streaming chat completion."""
        try:
            if provider.lower() == "anthropic":
                return await _anthropic_chat(
                    messages, user_message, model, default_system
                )
            elif provider.lower() == "openai":
                return await _openai_chat(messages, user_message, model, default_system)
            elif provider.lower() == "deepseek":
                return await _deepseek_chat(
                    messages, user_message, model, default_system
                )
            elif provider.lower() == "ollama":
                return await _ollama_chat(messages, user_message, model, default_system)
            else:
                return f"[Provider {provider} not yet implemented]"
        except Exception as e:
            return f"[Error: {e}]"

    # Chat loop
    turn_count = 0
    while True:
        try:
            # Show turn indicator for ongoing conversations
            if turn_count > 0:
                console.print(
                    "[dim]  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─[/dim]"
                )
                console.print()

            user_input = console.input("  [bold cyan]❯[/bold cyan] ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                cmd_arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

                if cmd in ("/exit", "/quit", "/q"):
                    # Auto-save session on exit
                    console.print()
                    if messages:
                        session_metadata["total_cost"] = _chat_costs[session_id][
                            "total_cost"
                        ]
                        session_metadata["total_tokens"] = _chat_costs[session_id][
                            "total_tokens"
                        ]
                        _save_session(session_id, messages, session_metadata)
                        console.print(
                            f"  [green]✓[/green] [dim]Session saved:[/dim] [cyan]{session_id}[/cyan]"
                        )
                    console.print()
                    console.print("  [dim]👋 Goodbye! See you next time.[/dim]")
                    console.print()
                    break

                elif cmd == "/clear":
                    messages.clear()
                    turn_count = 0
                    _chat_costs[session_id] = {
                        "total_cost": 0.0,
                        "total_tokens": {"input": 0, "output": 0},
                        "calls": 0,
                    }
                    console.print()
                    console.print(
                        "  [green]✓[/green] [dim]Conversation cleared. Start fresh![/dim]"
                    )
                    console.print()
                    continue

                elif cmd == "/save":
                    if not cmd_arg:
                        # Save to session file
                        session_metadata["total_cost"] = _chat_costs[session_id][
                            "total_cost"
                        ]
                        session_metadata["total_tokens"] = _chat_costs[session_id][
                            "total_tokens"
                        ]
                        _save_session(session_id, messages, session_metadata)
                        console.print()
                        console.print(
                            f"  [green]✓[/green] [dim]Session saved:[/dim] [cyan]{session_id}[/cyan]"
                        )
                        console.print()
                    else:
                        # Save to custom file
                        _save_conversation(messages, cmd_arg, session_id)
                        console.print()
                        console.print(
                            f"  [green]✓[/green] [dim]Exported to:[/dim] [cyan]{cmd_arg}[/cyan]"
                        )
                        console.print()
                    continue

                elif cmd == "/load":
                    if not cmd_arg:
                        console.print()
                        console.print("  [yellow]Usage:[/yellow] /load <session_id>")
                        console.print(
                            "  [dim]Use /sessions to see available sessions[/dim]"
                        )
                        console.print()
                        continue
                    loaded_messages, loaded_metadata = _load_session(cmd_arg)
                    if loaded_messages:
                        messages.clear()
                        messages.extend(loaded_messages)
                        session_metadata.update(loaded_metadata)
                        turn_count = len(messages) // 2
                        console.print()
                        console.print(
                            f"  [green]✓[/green] [dim]Loaded[/dim] [cyan]{len(messages)}[/cyan] [dim]messages from[/dim] [cyan]{cmd_arg}[/cyan]"
                        )
                        console.print()
                    else:
                        console.print()
                        console.print(
                            f"  [red]✗[/red] [dim]Session not found:[/dim] [yellow]{cmd_arg}[/yellow]"
                        )
                        console.print(
                            "  [dim]Use /sessions to see available sessions[/dim]"
                        )
                        console.print()
                    continue

                elif cmd == "/sessions":
                    sessions_dir = _get_sessions_dir()
                    session_files = list(sessions_dir.glob("*.json"))
                    if session_files:
                        console.print()
                        console.print("  [bold white]📁 Saved Sessions[/bold white]")
                        console.print(
                            "  [dim]────────────────────────────────────────[/dim]"
                        )
                        console.print()
                        for sf in sorted(
                            session_files, key=lambda x: x.stat().st_mtime, reverse=True
                        )[:10]:
                            mtime = datetime.fromtimestamp(sf.stat().st_mtime)
                            console.print(
                                f"    [bold cyan]{sf.stem}[/bold cyan]  [dim]{mtime.strftime('%Y-%m-%d %H:%M')}[/dim]"
                            )
                        console.print()
                        console.print(
                            "  [dim]Use[/dim] [magenta]/load <session_id>[/magenta] [dim]to restore a session[/dim]"
                        )
                        console.print()
                    else:
                        console.print()
                        console.print(
                            "  [dim]No saved sessions yet. Your sessions will appear here.[/dim]"
                        )
                        console.print()
                    continue

                elif cmd == "/cost":
                    cost_data = _chat_costs.get(session_id, {})
                    total_cost = cost_data.get("total_cost", 0.0)
                    tokens = cost_data.get("total_tokens", {"input": 0, "output": 0})
                    calls = cost_data.get("calls", 0)
                    console.print()
                    console.print("  [bold white]💰 Session Cost[/bold white]")
                    console.print(
                        "  [dim]────────────────────────────────────────[/dim]"
                    )
                    console.print()
                    console.print(
                        f"    [dim]Total Cost[/dim]     [bold green]${total_cost:.4f}[/bold green]"
                    )
                    console.print(
                        f"    [dim]Input Tokens[/dim]   {_format_tokens(tokens['input'])}"
                    )
                    console.print(
                        f"    [dim]Output Tokens[/dim]  {_format_tokens(tokens['output'])}"
                    )
                    console.print(f"    [dim]API Requests[/dim]   {calls}")
                    console.print()
                    continue

                elif cmd == "/help":
                    console.print()
                    console.print("  [bold white]📖 Available Commands[/bold white]")
                    console.print(
                        "  [dim]────────────────────────────────────────[/dim]"
                    )
                    console.print()
                    console.print(
                        "  [bold magenta]/exit[/bold magenta]          [dim]Exit chat (auto-saves session)[/dim]"
                    )
                    console.print(
                        "  [bold magenta]/clear[/bold magenta]         [dim]Clear conversation history[/dim]"
                    )
                    console.print(
                        "  [bold magenta]/save[/bold magenta] [dim][file][/dim]   [dim]Save session to file[/dim]"
                    )
                    console.print(
                        "  [bold magenta]/load[/bold magenta] [dim]<id>[/dim]     [dim]Load a previous session[/dim]"
                    )
                    console.print(
                        "  [bold magenta]/sessions[/bold magenta]      [dim]List all saved sessions[/dim]"
                    )
                    console.print(
                        "  [bold magenta]/cost[/bold magenta]          [dim]Show session cost summary[/dim]"
                    )
                    console.print(
                        "  [bold magenta]/help[/bold magenta]          [dim]Show this help message[/dim]"
                    )
                    console.print()
                    console.print(
                        "  [dim]Tip: Just type your message and press Enter to chat![/dim]"
                    )
                    console.print()
                    continue

                else:
                    console.print()
                    console.print(
                        f"  [yellow]⚠[/yellow] [dim]Unknown command:[/dim] [yellow]{cmd}[/yellow]"
                    )
                    console.print("  [dim]Type /help for available commands[/dim]")
                    console.print()
                    continue

            # Get AI response
            console.print()
            if stream and provider.lower() in (
                "anthropic",
                "openai",
                "deepseek",
                "ollama",
            ):
                # Streaming mode - show thinking briefly then stream
                console.print("  [bold green]◆[/bold green] ", end="")
                response = asyncio.run(chat_stream(user_input))
                console.print()  # Newline after streaming completes
            else:
                # Non-streaming mode with animated thinking indicator
                thinking_msg = _get_thinking_message()
                with console.status(
                    f"  [dim green]◇[/dim green] [dim italic]{thinking_msg}...[/dim italic]",
                    spinner="dots",
                    spinner_style="cyan",
                ):
                    response = asyncio.run(chat_completion(user_input))

                # Render response with elegant formatting
                console.print()
                console.print("  [bold green]◆[/bold green] ", end="")
                try:
                    md = Markdown(response, code_theme="monokai")
                    console.print(md)
                except Exception:
                    console.print(response)

            # Add to history
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": response})
            turn_count += 1

            # Show cost if enabled - elegant inline format
            if costs and provider.lower() in ("anthropic", "openai", "deepseek"):
                cost_data = _chat_costs.get(session_id, {})
                total_cost = cost_data.get("total_cost", 0)
                tokens = cost_data.get("total_tokens", {"input": 0, "output": 0})
                in_tokens = _format_tokens(tokens["input"])
                out_tokens = _format_tokens(tokens["output"])
                console.print()
                console.print(
                    f"  [dim]💰 ${total_cost:.4f}  •  ↑{in_tokens}  ↓{out_tokens}[/dim]"
                )

            console.print()

        except KeyboardInterrupt:
            console.print("\n\n[dim]Interrupted. Type /exit to quit.[/dim]\n")
        except EOFError:
            # Auto-save on EOF
            if messages:
                session_metadata["total_cost"] = _chat_costs[session_id]["total_cost"]
                session_metadata["total_tokens"] = _chat_costs[session_id][
                    "total_tokens"
                ]
                _save_session(session_id, messages, session_metadata)
            console.print("\n[dim]Goodbye![/dim]")
            break


async def _anthropic_chat(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
) -> str:
    """Chat using Anthropic API."""
    import os

    try:
        import anthropic
    except ImportError:
        return "[Error: anthropic package not installed. Run: pip install anthropic]"

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Build messages for API
    api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    api_messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=api_messages,
    )

    return response.content[0].text


async def _openai_chat(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
) -> str:
    """Chat using OpenAI API."""
    import os

    try:
        import openai
    except ImportError:
        return "[Error: openai package not installed. Run: pip install openai]"

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    api_messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=model,
        messages=api_messages,
        max_tokens=4096,
    )

    return response.choices[0].message.content


async def _ollama_chat(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
) -> str:
    """Chat using Ollama API."""
    import httpx

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    api_messages.append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": api_messages,
                "stream": False,
            },
        )

        if response.status_code != 200:
            return f"[Ollama error: {response.status_code}]"

        data = response.json()
        return data.get("message", {}).get("content", "[No response]")


async def _deepseek_chat(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
) -> str:
    """Chat using DeepSeek API (OpenAI-compatible)."""
    import os

    try:
        import openai
    except ImportError:
        return "[Error: openai package not installed. Run: pip install openai]"

    client = openai.OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    api_messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=model,
        messages=api_messages,
        max_tokens=4096,
    )

    return response.choices[0].message.content


# =============================================================================
# Streaming Chat Functions
# =============================================================================


async def _anthropic_stream(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
    session_id: str,
    track_costs: bool,
) -> str:
    """Stream chat using Anthropic API."""
    import os

    try:
        import anthropic
    except ImportError:
        return "[Error: anthropic package not installed]"

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Build messages for API
    api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    api_messages.append({"role": "user", "content": user_message})

    full_response = ""
    input_tokens = 0
    output_tokens = 0

    with client.messages.stream(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=api_messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

        # Get final message for token counts
        final_message = stream.get_final_message()
        if final_message and final_message.usage:
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

    # Track costs
    if track_costs and session_id in _chat_costs:
        cost = _estimate_cost("anthropic", model, input_tokens, output_tokens)
        _chat_costs[session_id]["total_cost"] += cost
        _chat_costs[session_id]["total_tokens"]["input"] += input_tokens
        _chat_costs[session_id]["total_tokens"]["output"] += output_tokens
        _chat_costs[session_id]["calls"] += 1

    return full_response


async def _openai_stream(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
    session_id: str,
    track_costs: bool,
) -> str:
    """Stream chat using OpenAI API."""
    import os

    try:
        import openai
    except ImportError:
        return "[Error: openai package not installed]"

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    api_messages.append({"role": "user", "content": user_message})

    full_response = ""
    input_tokens = 0
    output_tokens = 0

    stream = client.chat.completions.create(
        model=model,
        messages=api_messages,
        max_tokens=4096,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            full_response += text
        if chunk.usage:
            input_tokens = chunk.usage.prompt_tokens
            output_tokens = chunk.usage.completion_tokens

    # Track costs
    if track_costs and session_id in _chat_costs:
        cost = _estimate_cost("openai", model, input_tokens, output_tokens)
        _chat_costs[session_id]["total_cost"] += cost
        _chat_costs[session_id]["total_tokens"]["input"] += input_tokens
        _chat_costs[session_id]["total_tokens"]["output"] += output_tokens
        _chat_costs[session_id]["calls"] += 1

    return full_response


async def _deepseek_stream(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
    session_id: str,
    track_costs: bool,
) -> str:
    """Stream chat using DeepSeek API (OpenAI-compatible)."""
    import os

    try:
        import openai
    except ImportError:
        return "[Error: openai package not installed]"

    client = openai.OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    api_messages.append({"role": "user", "content": user_message})

    full_response = ""

    # Estimate tokens from text length (DeepSeek doesn't always return usage in stream)
    input_text = system_prompt + " ".join(m["content"] for m in api_messages)
    estimated_input_tokens = len(input_text) // 4  # Rough estimate

    stream = client.chat.completions.create(
        model=model,
        messages=api_messages,
        max_tokens=4096,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            print(text, end="", flush=True)
            full_response += text

    estimated_output_tokens = len(full_response) // 4

    # Track costs
    if track_costs and session_id in _chat_costs:
        cost = _estimate_cost(
            "deepseek", model, estimated_input_tokens, estimated_output_tokens
        )
        _chat_costs[session_id]["total_cost"] += cost
        _chat_costs[session_id]["total_tokens"]["input"] += estimated_input_tokens
        _chat_costs[session_id]["total_tokens"]["output"] += estimated_output_tokens
        _chat_costs[session_id]["calls"] += 1

    return full_response


async def _ollama_stream(
    messages: list[dict[str, str]],
    user_message: str,
    model: str,
    system_prompt: str,
) -> str:
    """Stream chat using Ollama API."""
    import json

    import httpx

    # Build messages for API
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )
    api_messages.append({"role": "user", "content": user_message})

    full_response = ""

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": api_messages,
                "stream": True,
            },
        ) as response:
            if response.status_code != 200:
                return f"[Ollama error: {response.status_code}]"

            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            text = data["message"]["content"]
                            print(text, end="", flush=True)
                            full_response += text
                    except json.JSONDecodeError:
                        pass

    return full_response


def _save_conversation(
    messages: list[dict[str, str]],
    filename: str,
    session_id: str,
) -> None:
    """Save conversation to file."""
    from datetime import datetime

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Paracle Meta Chat - Session {session_id}\n")
        f.write(f"# Saved: {datetime.now().isoformat()}\n\n")

        for msg in messages:
            role = "You" if msg["role"] == "user" else "Assistant"
            f.write(f"## {role}\n\n{msg['content']}\n\n")


# =============================================================================
# Plan Mode
# =============================================================================


@meta.command("plan")
@click.argument("goal", required=False)
@click.option(
    "--provider",
    "-p",
    default="anthropic",
    help="AI provider (anthropic, openai, ollama)",
)
@click.option("--model", "-m", help="Model to use (provider-specific)")
@click.option(
    "--execute", "-e", is_flag=True, help="Auto-execute the plan after creation"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    default=True,
    help="Interactive mode with step approval (default)",
)
def meta_plan(
    goal: str | None,
    provider: str,
    model: str | None,
    execute: bool,
    interactive: bool,
) -> None:
    """Create and execute structured plans with AI.

    Plan mode decomposes complex tasks into steps and optionally executes them.

    Examples:
        paracle meta plan "Build a REST API"           # Create plan only
        paracle meta plan "Add auth" -e                # Create and execute
        paracle meta plan                              # Interactive mode

    Commands during planning:
        /execute      - Execute current plan
        /step <n>     - Execute step N only
        /show         - Show current plan
        /save <file>  - Save plan to file
        /exit         - Exit planning
    """
    import asyncio

    # Check provider
    providers_status = _check_providers()
    provider_map = {
        "anthropic": "Anthropic",
        "openai": "OpenAI",
        "ollama": "Ollama",
    }

    provider_name = provider_map.get(provider.lower(), provider)
    if provider_name in providers_status and not providers_status[provider_name]:
        if provider.lower() == "ollama":
            console.print("[red]Error:[/red] Ollama is not running")
            console.print("Start Ollama with: ollama serve")
        else:
            env_var = f"{provider.upper()}_API_KEY"
            console.print(f"[red]Error:[/red] {provider_name} not configured")
            console.print(f"Set {env_var} environment variable")
        raise SystemExit(1)

    # Default models
    default_models = {
        "anthropic": "claude-sonnet-4-20250514",
        "openai": "gpt-4o",
        "ollama": "llama3",
    }
    model = model or default_models.get(provider.lower(), "gpt-4o")

    console.print(
        Panel(
            "[bold]Paracle Meta Plan Mode[/bold]\n"
            f"Provider: {provider_name} | Model: {model}",
            title="paracle meta plan",
        )
    )

    # Get goal if not provided
    if not goal:
        console.print("\n[dim]Enter your goal (what you want to achieve):[/dim]")
        goal = console.input("[bold cyan]Goal>[/bold cyan] ").strip()
        if not goal:
            console.print("[red]No goal provided. Exiting.[/red]")
            raise SystemExit(1)

    # Create plan
    console.print(f"\n[bold]Creating plan for:[/bold] {goal}\n")

    with console.status(
        "[bold cyan]Planning...[/bold cyan]",
        spinner="dots",
    ):
        plan = asyncio.run(_create_plan(goal, provider, model))

    if not plan:
        console.print("[red]Failed to create plan.[/red]")
        raise SystemExit(1)

    # Display plan
    _display_plan(plan)

    # Execute if requested
    if execute:
        console.print("\n[bold]Executing plan...[/bold]\n")
        asyncio.run(_execute_plan_interactive(plan, provider, model))
    elif interactive:
        # Interactive planning loop
        _plan_interactive_loop(plan, provider, model)


async def _create_plan(
    goal: str,
    provider: str,
    model: str,
) -> dict | None:
    """Create a plan using AI."""
    system_prompt = """You are a strategic planning assistant. Decompose the goal into clear, actionable steps.

Output plans in JSON format:
{
    "goal": "the goal",
    "summary": "brief approach summary",
    "steps": [
        {
            "id": "step_1",
            "description": "what this step does",
            "action": "specific action",
            "complexity": "low|medium|high"
        }
    ],
    "success_criteria": "how to know it's done"
}"""

    messages: list[dict[str, str]] = []
    user_message = f"Create a detailed plan for: {goal}"

    if provider.lower() == "anthropic":
        response = await _anthropic_chat(messages, user_message, model, system_prompt)
    elif provider.lower() == "openai":
        response = await _openai_chat(messages, user_message, model, system_prompt)
    elif provider.lower() == "ollama":
        response = await _ollama_chat(messages, user_message, model, system_prompt)
    else:
        return None

    # Parse JSON from response
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            return json_module.loads(response[start:end])
    except Exception:
        pass

    # Fallback: simple structure
    return {
        "goal": goal,
        "summary": response[:200],
        "steps": [
            {
                "id": "step_1",
                "description": response,
                "action": response,
                "complexity": "medium",
            }
        ],
        "success_criteria": "Review the output",
    }


def _display_plan(plan: dict) -> None:
    """Display a plan in formatted output."""
    console.print(f"\n[bold green]Plan:[/bold green] {plan.get('goal', 'Unknown')}")
    console.print(f"[dim]{plan.get('summary', '')}[/dim]\n")

    steps = plan.get("steps", [])
    table = Table(title=f"Steps ({len(steps)} total)")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Description", style="white")
    table.add_column("Complexity", style="yellow", width=10)
    table.add_column("Status", style="green", width=10)

    for i, step in enumerate(steps, 1):
        status = step.get("status", "pending")
        status_icon = {
            "pending": "[dim]○[/dim]",
            "in_progress": "[yellow]◐[/yellow]",
            "completed": "[green]●[/green]",
            "failed": "[red]✗[/red]",
        }.get(status, "[dim]○[/dim]")

        table.add_row(
            str(i),
            step.get("description", ""),
            step.get("complexity", "medium"),
            status_icon,
        )

    console.print(table)

    if plan.get("success_criteria"):
        console.print(f"\n[bold]Success Criteria:[/bold] {plan['success_criteria']}")


def _plan_interactive_loop(plan: dict, provider: str, model: str) -> None:
    """Interactive planning loop."""
    import asyncio

    console.print(
        "\n[dim]Commands: /execute, /step <n>, /show, /save <file>, /help, /exit[/dim]\n"
    )

    while True:
        try:
            user_input = console.input("[bold cyan]Plan>[/bold cyan] ").strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                cmd_parts = user_input.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                cmd_arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

                if cmd in ("/exit", "/quit", "/q"):
                    console.print("\n[dim]Goodbye![/dim]")
                    break

                elif cmd == "/show":
                    _display_plan(plan)

                elif cmd == "/execute":
                    console.print("\n[bold]Executing plan...[/bold]\n")
                    asyncio.run(_execute_plan_interactive(plan, provider, model))

                elif cmd == "/step":
                    if not cmd_arg:
                        console.print("[red]Usage:[/red] /step <number>")
                        continue
                    try:
                        step_num = int(cmd_arg) - 1
                        steps = plan.get("steps", [])
                        if 0 <= step_num < len(steps):
                            console.print(
                                f"\n[bold]Executing step {step_num + 1}...[/bold]\n"
                            )
                            asyncio.run(_execute_step(steps[step_num], provider, model))
                            steps[step_num]["status"] = "completed"
                            _display_plan(plan)
                        else:
                            console.print(
                                f"[red]Invalid step number. Range: 1-{len(steps)}[/red]"
                            )
                    except ValueError:
                        console.print("[red]Invalid step number.[/red]")

                elif cmd == "/save":
                    if not cmd_arg:
                        console.print("[red]Usage:[/red] /save <filename>")
                        continue
                    _save_plan(plan, cmd_arg)
                    console.print(f"[green]Plan saved to {cmd_arg}[/green]")

                elif cmd == "/help":
                    console.print("\n[bold]Plan Commands:[/bold]")
                    console.print("  /execute      - Execute all steps")
                    console.print("  /step <n>     - Execute step N")
                    console.print("  /show         - Show current plan")
                    console.print("  /save <file>  - Save plan to file")
                    console.print("  /exit         - Exit planning\n")

                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                    console.print("Type /help for available commands.")

            else:
                # Treat as new goal - create new plan
                console.print(f"\n[bold]Creating new plan for:[/bold] {user_input}\n")
                with console.status(
                    "[bold cyan]Planning...[/bold cyan]", spinner="dots"
                ):
                    import asyncio

                    new_plan = asyncio.run(_create_plan(user_input, provider, model))
                if new_plan:
                    plan.clear()
                    plan.update(new_plan)
                    _display_plan(plan)
                else:
                    console.print("[red]Failed to create plan.[/red]")

        except KeyboardInterrupt:
            console.print("\n\n[dim]Interrupted. Type /exit to quit.[/dim]\n")
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break


async def _execute_plan_interactive(plan: dict, provider: str, model: str) -> None:
    """Execute plan steps interactively."""
    steps = plan.get("steps", [])

    for i, step in enumerate(steps, 1):
        console.print(
            f"\n[bold]Step {i}/{len(steps)}:[/bold] {step.get('description', '')}"
        )
        step["status"] = "in_progress"

        with console.status("[bold cyan]Executing...[/bold cyan]", spinner="dots"):
            result = await _execute_step(step, provider, model)

        step["status"] = "completed"
        step["result"] = result

        console.print(
            f"[green]Result:[/green] {result[:500]}..."
            if len(result) > 500
            else f"[green]Result:[/green] {result}"
        )

    console.print("\n[bold green]Plan execution complete![/bold green]")
    _display_plan(plan)


async def _execute_step(step: dict, provider: str, model: str) -> str:
    """Execute a single step."""
    system_prompt = "You are executing a task step. Provide a concise result or output."
    messages: list[dict[str, str]] = []
    user_message = (
        f"Execute this step:\n\n{step.get('action', step.get('description', ''))}"
    )

    if provider.lower() == "anthropic":
        return await _anthropic_chat(messages, user_message, model, system_prompt)
    elif provider.lower() == "openai":
        return await _openai_chat(messages, user_message, model, system_prompt)
    elif provider.lower() == "ollama":
        return await _ollama_chat(messages, user_message, model, system_prompt)

    return "[Step execution not available for this provider]"


def _save_plan(plan: dict, filename: str) -> None:
    """Save plan to file."""
    import json as json_module
    from datetime import datetime

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Paracle Plan\n")
        f.write(f"# Saved: {datetime.now().isoformat()}\n\n")
        f.write(f"## Goal\n{plan.get('goal', '')}\n\n")
        f.write(f"## Summary\n{plan.get('summary', '')}\n\n")
        f.write("## Steps\n")
        for i, step in enumerate(plan.get("steps", []), 1):
            status = step.get("status", "pending")
            icon = "●" if status == "completed" else "○"
            f.write(f"{i}. {icon} {step.get('description', '')}\n")
            if step.get("result"):
                f.write(f"   Result: {step['result']}\n")
        f.write(f"\n## Success Criteria\n{plan.get('success_criteria', '')}\n")
        f.write(f"\n---\n\n```json\n{json_module.dumps(plan, indent=2)}\n```\n")


# =============================================================================
# System Skills Management
# =============================================================================


@meta.group("skills")
def meta_skills() -> None:
    """Manage system-wide framework skills.

    System skills are paracle_meta capabilities available to all projects:
    - meta-generation: AI-powered artifact generation
    - meta-learning: Continuous improvement system
    - meta-capabilities: Advanced AI capabilities

    These are stored in platform-specific directories and are separate
    from user project skills in .parac/agents/skills/.

    Commands:
        paracle meta skills list           - List system skills
        paracle meta skills init           - Initialize skills directory
        paracle meta skills install-bundled - Install framework skills
        paracle meta skills show <name>    - Show skill details
    """


@meta_skills.command("init")
def skills_init() -> None:
    """Initialize system skills directory.

    Creates the platform-specific skills directory if it doesn't exist.
    """
    from paracle_core.paths import ensure_system_directories, get_system_paths

    paths = get_system_paths()

    if paths.skills_dir.exists():
        console.print("[yellow]System skills directory already exists:[/yellow]")
        console.print(f"  {paths.skills_dir}")
        return

    try:
        ensure_system_directories()
        console.print("[green]OK[/green] Created system skills directory:")
        console.print(f"  {paths.skills_dir}")
        console.print("\nNext: paracle meta skills install-bundled")
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to create directory: {e}")
        raise SystemExit(1)


@meta_skills.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def skills_list(verbose: bool) -> None:
    """List system-wide meta skills.

    Shows skills installed in the system directory.
    """
    from paracle_skills import SkillLoader

    try:
        loader = SkillLoader.system_only()
        skill_list = loader.load_all()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    system_dir = get_system_skills_dir()

    if not skill_list:
        console.print("[yellow]No system skills found.[/yellow]")
        console.print(f"\nDirectory: {system_dir}")
        console.print("\nInstall bundled skills: paracle meta skills install-bundled")
        return

    table = Table(title=f"System Meta Skills ({len(skill_list)} found)")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="green")
    table.add_column("Level", style="yellow")
    if verbose:
        table.add_column("Description")

    for skill in sorted(skill_list, key=lambda s: s.name):
        row = [skill.name, skill.metadata.category.value, skill.metadata.level.value]
        if verbose:
            desc = (
                skill.description[:40] + "..."
                if len(skill.description) > 40
                else skill.description
            )
            row.append(desc)
        table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]Directory: {system_dir}[/dim]")


@meta_skills.command("show")
@click.argument("skill_name")
@click.option("--raw", is_flag=True, help="Show raw SKILL.md content")
def skills_show(skill_name: str, raw: bool) -> None:
    """Show details for a system skill.

    Examples:
        paracle meta skills show meta-generation
        paracle meta skills show meta-learning --raw
    """
    from paracle_skills import SkillLoader

    system_dir = get_system_skills_dir()
    skill_path = system_dir / skill_name / "SKILL.md"

    if not skill_path.exists():
        console.print(f"[red]Error:[/red] System skill '{skill_name}' not found")
        console.print(f"\nSearched: {skill_path}")
        console.print("\nList available: paracle meta skills list")
        raise SystemExit(1)

    if raw:
        console.print(skill_path.read_text(encoding="utf-8"))
        return

    loader = SkillLoader.system_only()

    try:
        skill = loader.load_skill(skill_path, source="system")
    except Exception as e:
        console.print(f"[red]Error loading skill:[/red] {e}")
        raise SystemExit(1)

    # Display skill info
    console.print(
        Panel(
            f"[bold cyan]{skill.metadata.display_name or skill.name}[/bold cyan]",
            title="System Skill",
        )
    )

    console.print(f"\n[bold]Name:[/bold] {skill.name}")
    console.print(f"[bold]Description:[/bold] {skill.description}")
    console.print(f"[bold]Category:[/bold] {skill.metadata.category.value}")
    console.print(f"[bold]Level:[/bold] {skill.metadata.level.value}")

    if skill.metadata.tags:
        console.print(f"[bold]Tags:[/bold] {', '.join(skill.metadata.tags)}")

    if skill.metadata.capabilities:
        console.print("\n[bold]Capabilities:[/bold]")
        for cap in skill.metadata.capabilities:
            console.print(f"  - {cap}")

    if skill.allowed_tools:
        console.print(f"\n[bold]Allowed Tools:[/bold] {skill.allowed_tools}")

    console.print(f"\n[bold]Path:[/bold] {skill.source_path}")


@meta_skills.command("install-bundled")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing skills")
def skills_install_bundled(force: bool) -> None:
    """Install bundled paracle_meta skills to system directory.

    Installs the framework-provided meta skills:
    - meta-generation: AI-powered artifact generation
    - meta-learning: Continuous improvement system
    - meta-capabilities: Advanced AI capabilities

    Examples:
        paracle meta skills install-bundled
        paracle meta skills install-bundled -f
    """
    import shutil
    from importlib.resources import files

    system_dir = get_system_skills_dir()

    # Ensure system directory exists
    system_dir.mkdir(parents=True, exist_ok=True)

    # Get bundled skills from paracle_meta package
    try:
        bundled_skills_path = files("paracle_meta") / "skills"
        if not bundled_skills_path.is_dir():
            console.print("[red]Error:[/red] Bundled skills not found in paracle_meta")
            console.print("This may indicate an incomplete installation.")
            raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Could not locate bundled skills: {e}")
        raise SystemExit(1)

    # Find and install each bundled skill
    installed = []
    skipped = []

    for skill_dir in bundled_skills_path.iterdir():
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").is_file():
            continue

        skill_name = skill_dir.name
        target_dir = system_dir / skill_name

        if target_dir.exists():
            if force:
                shutil.rmtree(target_dir)
            else:
                skipped.append(skill_name)
                continue

        # Copy skill to system directory
        shutil.copytree(skill_dir, target_dir)
        installed.append(skill_name)

    # Report results
    if installed:
        console.print(f"\n[green]OK[/green] Installed {len(installed)} meta skill(s):")
        for name in installed:
            console.print(f"  + {name}")

    if skipped:
        console.print(f"\n[yellow]Skipped[/yellow] {len(skipped)} existing skill(s):")
        for name in skipped:
            console.print(f"  - {name} (use -f to overwrite)")

    if not installed and not skipped:
        console.print("[yellow]No bundled skills found.[/yellow]")
    else:
        console.print(f"\n[bold]System skills directory:[/bold] {system_dir}")


@meta_skills.command("remove")
@click.argument("skill_name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def skills_remove(skill_name: str, force: bool) -> None:
    """Remove a skill from system directory.

    Examples:
        paracle meta skills remove my-skill
        paracle meta skills remove my-skill -f
    """
    import shutil

    system_dir = get_system_skills_dir()
    skill_dir = system_dir / skill_name

    if not skill_dir.exists():
        console.print(f"[red]Error:[/red] System skill '{skill_name}' not found")
        raise SystemExit(1)

    if not force:
        console.print(f"[yellow]Remove system skill '{skill_name}'?[/yellow]")
        console.print(f"  {skill_dir}")
        if not click.confirm("Continue?"):
            console.print("Cancelled.")
            return

    shutil.rmtree(skill_dir)
    console.print(f"[green]OK[/green] Removed '{skill_name}' from system")


# =============================================================================
# AI Generation (placeholder for future)
# =============================================================================


@meta.group("generate")
def meta_generate() -> None:
    """Generate Paracle artifacts with AI.

    Use AI to generate agents, workflows, skills, and policies
    from natural language descriptions.

    Examples:
        paracle meta generate agent SecurityAuditor \\
            --desc "Reviews code for security vulnerabilities"

        paracle meta generate workflow review-pipeline \\
            --desc "Multi-stage code review process"
    """


@meta_generate.command("agent")
@click.argument("name")
@click.option("--desc", "-d", required=True, help="Description of the agent")
@click.option("--provider", "-p", default="anthropic", help="AI provider to use")
def generate_agent(name: str, desc: str, provider: str) -> None:
    """Generate an agent specification with AI.

    **DEPRECATED**: Use 'paracle agents create --ai-enhance' instead.

    This command is deprecated and will be removed in a future version.
    Please use the new consolidated command:

        paracle agents create <name> --role "<desc>" --ai-enhance

    Examples:
        # Old (deprecated):
        paracle meta generate agent SecurityAuditor \\
            --desc "Reviews code for security vulnerabilities"

        # New (recommended):
        paracle agents create security-auditor \\
            --role "Reviews code for security vulnerabilities" \\
            --ai-enhance --ai-provider anthropic
    """
    console.print("[yellow]⚠ DEPRECATED:[/yellow] This command is deprecated")
    console.print()
    console.print("[cyan]Please use instead:[/cyan]")
    console.print(f"  paracle agents create {name.lower().replace(' ', '-')} \\")
    console.print(f'    --role "{desc}" \\')
    console.print(f"    --ai-enhance --ai-provider {provider}")
    console.print()
    console.print("[dim]This command will be removed in a future version.[/dim]")
    console.print()

    if not click.confirm("Continue with deprecated command?", default=False):
        raise SystemExit(1)

    console.print(f"[yellow]Generating agent '{name}'...[/yellow]")
    console.print(f"Description: {desc}")
    console.print(f"Provider: {provider}")
    console.print(
        "\n[dim]Note: Full generation requires AI provider configuration.[/dim]"
    )
    console.print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")


@meta_generate.command("workflow")
@click.argument("name")
@click.option("--desc", "-d", required=True, help="Description of the workflow")
@click.option("--provider", "-p", default="anthropic", help="AI provider to use")
def generate_workflow(name: str, desc: str, provider: str) -> None:
    """Generate a workflow specification with AI.

    **DEPRECATED**: Use 'paracle workflow create --ai-enhance' instead.

    This command is deprecated and will be removed in a future version.
    Please use the new consolidated command:

        paracle workflow create <name> --description "<desc>" --ai-enhance

    Examples:
        # Old (deprecated):
        paracle meta generate workflow review-pipeline \\
            --desc "Multi-stage code review with security checks"

        # New (recommended):
        paracle workflow create review-pipeline \\
            --description "Multi-stage code review with security checks" \\
            --ai-enhance --ai-provider anthropic
    """
    console.print("[yellow]⚠ DEPRECATED:[/yellow] This command is deprecated")
    console.print()
    console.print("[cyan]Please use instead:[/cyan]")
    console.print(f"  paracle workflow create {name.lower().replace(' ', '-')} \\")
    console.print(f'    --description "{desc}" \\')
    console.print(f"    --ai-enhance --ai-provider {provider}")
    console.print()
    console.print("[dim]This command will be removed in a future version.[/dim]")
    console.print()

    if not click.confirm("Continue with deprecated command?", default=False):
        raise SystemExit(1)

    console.print(f"[yellow]Generating workflow '{name}'...[/yellow]")
    console.print(f"Description: {desc}")
    console.print(f"Provider: {provider}")
    console.print(
        "\n[dim]Note: Full generation requires AI provider configuration.[/dim]"
    )


# =============================================================================
# Learning & Feedback (placeholder for future)
# =============================================================================


@meta.group("learn")
def meta_learn() -> None:
    """Manage learning and feedback.

    Track generation quality, record feedback, and improve
    templates over time.

    Examples:
        paracle meta learn stats     - Show learning statistics
        paracle meta learn feedback  - Record feedback
        paracle meta learn evolve    - Evolve templates
    """


@meta_learn.command("stats")
def learn_stats() -> None:
    """Show learning statistics.

    Displays generation quality, feedback counts, and trends.
    """
    console.print(
        Panel(
            "[bold]Learning Statistics[/bold]",
            title="paracle meta learn stats",
        )
    )

    console.print("\n[dim]Learning system not yet configured.[/dim]")
    console.print("Statistics will appear here after generating artifacts.")


@meta_learn.command("feedback")
@click.argument("artifact_id")
@click.option("--rating", "-r", type=int, required=True, help="Rating 1-5")
@click.option("--comment", "-c", help="Optional feedback comment")
def learn_feedback(artifact_id: str, rating: int, comment: str | None) -> None:
    """Record feedback for a generated artifact.

    Examples:
        paracle meta learn feedback abc123 --rating 4
        paracle meta learn feedback abc123 -r 5 -c "Great output"
    """
    if not 1 <= rating <= 5:
        console.print("[red]Error:[/red] Rating must be 1-5")
        raise SystemExit(1)

    console.print(f"Recording feedback for {artifact_id}:")
    console.print(f"  Rating: {'⭐' * rating}")
    if comment:
        console.print(f"  Comment: {comment}")
    console.print("\n[dim]Feedback recorded (learning system placeholder).[/dim]")
