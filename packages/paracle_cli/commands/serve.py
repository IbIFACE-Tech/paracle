"""Paracle serve command - Start API server.

Priority 0 - Essential command for Phase 4.
"""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to",
    show_default=True,
)
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Port to bind the server to",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload (development only)",
)
@click.option(
    "--workers",
    "-w",
    default=1,
    type=int,
    help="Number of worker processes (production)",
    show_default=True,
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default="info",
    help="Logging level",
    show_default=True,
)
@click.option(
    "--access-log/--no-access-log",
    default=True,
    help="Enable/disable access logs",
)
def serve(
    host: str,
    port: int,
    reload: bool,
    workers: int,
    log_level: str,
    access_log: bool,
) -> None:
    """Start the Paracle API server.

    This command starts a production-ready FastAPI server with:
    - Full security middleware stack (OWASP headers, CORS, rate limiting)
    - JWT authentication
    - Request logging with correlation IDs
    - Health checks and metrics
    - ISO 42001 audit trail

    Examples:

        # Development mode with auto-reload
        $ paracle serve --reload

        # Production mode with 4 workers
        $ paracle serve --host 0.0.0.0 --port 8000 --workers 4

        # Custom logging
        $ paracle serve --log-level debug

    Environment Variables:

        PARACLE_HOST            - Server host (default: 127.0.0.1)
        PARACLE_PORT            - Server port (default: 8000)
        PARACLE_WORKERS         - Number of workers (default: 1)
        PARACLE_LOG_LEVEL       - Log level (default: info)
        PARACLE_ENVIRONMENT     - Environment (development, staging, production)
        PARACLE_SECRET_KEY      - JWT secret key (required for production)
        PARACLE_CORS_ORIGINS    - Allowed CORS origins (comma-separated)
    """
    try:
        # Check if uvicorn is installed
        try:
            import uvicorn
        except ImportError:
            console.print(
                "[red]Error:[/red] uvicorn is not installed.\n"
                "Install with: [cyan]pip install uvicorn[/cyan]"
            )
            sys.exit(1)

        # Display startup banner
        _display_startup_banner(host, port, reload, workers, log_level)

        # Validate configuration
        _validate_configuration(host, port, workers, reload)

        # Prepare uvicorn config
        uvicorn_config = {
            "app": "paracle_api.main:app",
            "host": host,
            "port": port,
            "log_level": log_level,
            "access_log": access_log,
        }

        # Development mode
        if reload:
            console.print(
                "\n[yellow]⚠️  Development mode with auto-reload enabled[/yellow]"
            )
            console.print("[yellow]   Not suitable for production![/yellow]\n")
            uvicorn_config["reload"] = True
            uvicorn_config["reload_dirs"] = ["packages"]

        # Production mode
        else:
            if workers > 1:
                console.print(
                    f"\n[green]✓[/green] Production mode with {workers} workers\n"
                )
                uvicorn_config["workers"] = workers
            else:
                console.print("\n[green]✓[/green] Production mode (single worker)\n")

        # Start server
        console.print("[bold cyan]Starting Paracle API server...[/bold cyan]")
        console.print(f"Listening on [bold]http://{host}:{port}[/bold]\n")

        uvicorn.run(**uvicorn_config)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Server stopped by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error starting server:[/red] {e}")
        sys.exit(1)


def _display_startup_banner(
    host: str,
    port: int,
    reload: bool,
    workers: int,
    log_level: str,
) -> None:
    """Display startup banner with configuration."""
    # Create configuration table
    config_table = Table(show_header=False, box=None, padding=(0, 2))
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config_table.add_row("Host", host)
    config_table.add_row("Port", str(port))
    config_table.add_row("Mode", "Development (reload)" if reload else "Production")
    config_table.add_row("Workers", str(workers) if not reload else "1 (reload mode)")
    config_table.add_row("Log Level", log_level.upper())

    panel = Panel(
        config_table,
        title="[bold]🚀 Paracle API Server[/bold]",
        subtitle="v0.0.1",
        border_style="blue",
    )

    console.print(panel)


def _validate_configuration(
    host: str,
    port: int,
    workers: int,
    reload: bool,
) -> None:
    """Validate server configuration."""
    import os

    # Warn about binding to all interfaces
    if host in ["0.0.0.0", "::"]:
        console.print(
            "[yellow]⚠️  Warning:[/yellow] Server will be accessible from all network interfaces"
        )

    # Validate port range
    if not (1 <= port <= 65535):
        console.print(f"[red]Error:[/red] Invalid port number: {port}")
        console.print("Port must be between 1 and 65535")
        sys.exit(1)

    # Check if port is likely privileged
    if port < 1024 and os.geteuid() != 0 if hasattr(os, "geteuid") else False:
        console.print(
            f"[yellow]⚠️  Warning:[/yellow] Port {port} may require root privileges"
        )

    # Validate workers
    if workers < 1:
        console.print("[red]Error:[/red] Workers must be >= 1")
        sys.exit(1)

    if reload and workers > 1:
        console.print(
            "[yellow]⚠️  Warning:[/yellow] Auto-reload mode ignores --workers option"
        )

    # Check production configuration
    env = os.getenv("PARACLE_ENVIRONMENT", "development")
    if env == "production":
        secret_key = os.getenv("PARACLE_SECRET_KEY")
        if not secret_key or len(secret_key) < 32:
            console.print(
                "[red]Error:[/red] PARACLE_SECRET_KEY must be set in production "
                "and at least 32 characters"
            )
            sys.exit(1)

        if reload:
            console.print(
                "[red]Error:[/red] Auto-reload mode is not allowed in production"
            )
            sys.exit(1)

        if host == "127.0.0.1":
            console.print(
                "[yellow]⚠️  Warning:[/yellow] Production server bound to localhost only"
            )
