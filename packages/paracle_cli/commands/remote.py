"""CLI commands for remote development and SSH support."""

import asyncio
import sys

import click
import yaml
from paracle_core.parac.state import find_parac_root
from paracle_transport import RemoteConfig, RemotesConfig, SSHTransport
from paracle_transport.remote_config import TunnelConfig


@click.group()
def remote():
    """Manage remote Paracle instances."""
    pass


@remote.command("list")
def list_remotes():
    """List all configured remote instances."""
    try:
        remotes_config = _load_remotes_config()

        if not remotes_config.remotes:
            click.echo("No remote instances configured.")
            click.echo(
                "\nAdd a remote with: paracle remote add <name> <host> <workspace>"
            )
            return

        click.echo("Configured remotes:\n")
        for name, config in remotes_config.remotes.items():
            is_default = " (default)" if name == remotes_config.default else ""
            click.echo(f"  {name}{is_default}")
            click.echo(f"    Host: {config.host}")
            click.echo(f"    Workspace: {config.workspace}")
            click.echo(f"    Port: {config.port}")
            if config.identity_file:
                click.echo(f"    Identity: {config.identity_file}")
            if config.tunnels:
                click.echo(f"    Tunnels: {len(config.tunnels)}")
                for tunnel in config.tunnels:
                    click.echo(
                        f"      - localhost:{tunnel.local} -> remote:{tunnel.remote}"
                    )
            click.echo()

    except FileNotFoundError:
        click.echo("No remotes configured yet.")
        click.echo("\nAdd a remote with: paracle remote add <name> <host> <workspace>")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@remote.command("add")
@click.argument("name")
@click.argument("host")
@click.argument("workspace")
@click.option("--port", default=22, help="SSH port (default: 22)")
@click.option("--identity-file", help="Path to SSH private key")
@click.option(
    "--tunnel",
    "tunnels",
    multiple=True,
    help="Add tunnel (format: local:remote, e.g., 8000:8000)",
)
@click.option("--set-default", is_flag=True, help="Set as default remote")
def add_remote(
    name: str,
    host: str,
    workspace: str,
    port: int,
    identity_file: str | None,
    tunnels: tuple[str, ...],
    set_default: bool,
):
    """Add a new remote instance.

    Example:
        paracle remote add production user@prod.com /opt/paracle \\
            --tunnel 8000:8000 --set-default
    """
    try:
        # Parse tunnels
        tunnel_configs = []
        for tunnel_str in tunnels:
            try:
                local, remote = tunnel_str.split(":")
                tunnel_configs.append(
                    TunnelConfig(
                        local=int(local),
                        remote=int(remote),
                        description=f"Tunnel {local}→{remote}",
                    )
                )
            except ValueError:
                click.echo(f"Invalid tunnel format: {tunnel_str}", err=True)
                click.echo("Expected format: local:remote (e.g., 8000:8000)")
                sys.exit(1)

        # Create remote config
        remote_config = RemoteConfig(
            name=name,
            host=host,
            workspace=workspace,
            port=port,
            identity_file=identity_file,
            tunnels=tunnel_configs,
        )

        # Load existing config
        remotes_config = _load_remotes_config()

        # Add new remote
        remotes_config.remotes[name] = remote_config

        # Set default if requested
        if set_default or not remotes_config.default:
            remotes_config.default = name

        # Save config
        _save_remotes_config(remotes_config)

        click.echo(f"✓ Added remote '{name}'")
        if set_default or not remotes_config.default:
            click.echo("✓ Set as default remote")

        # Test connection
        if click.confirm("\nTest connection now?", default=True):
            click.echo("Testing connection...")
            asyncio.run(_test_connection(remote_config))

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@remote.command("remove")
@click.argument("name")
@click.option("--force", is_flag=True, help="Skip confirmation")
def remove_remote(name: str, force: bool):
    """Remove a remote instance."""
    try:
        remotes_config = _load_remotes_config()

        if name not in remotes_config.remotes:
            click.echo(f"Remote '{name}' not found", err=True)
            sys.exit(1)

        if not force:
            if not click.confirm(f"Remove remote '{name}'?"):
                click.echo("Cancelled")
                return

        del remotes_config.remotes[name]

        # Clear default if it was removed
        if remotes_config.default == name:
            remotes_config.default = None

        _save_remotes_config(remotes_config)
        click.echo(f"✓ Removed remote '{name}'")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@remote.command("test")
@click.argument("name")
def test_remote(name: str):
    """Test connection to a remote instance."""
    try:
        remotes_config = _load_remotes_config()
        remote_config = remotes_config.get_remote(name)

        click.echo(f"Testing connection to '{name}'...")
        asyncio.run(_test_connection(remote_config))

    except KeyError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@remote.command("set-default")
@click.argument("name")
def set_default(name: str):
    """Set default remote instance."""
    try:
        remotes_config = _load_remotes_config()

        if name not in remotes_config.remotes:
            click.echo(f"Remote '{name}' not found", err=True)
            sys.exit(1)

        remotes_config.default = name
        _save_remotes_config(remotes_config)

        click.echo(f"✓ Set '{name}' as default remote")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def _test_connection(config: RemoteConfig) -> None:
    """Test SSH connection and tunnels.

    Args:
        config: Remote configuration to test.
    """
    try:
        async with SSHTransport(config) as transport:
            click.echo(f"  ✓ Connected to {config.host}")
            click.echo(f"  ✓ Verified workspace at {config.workspace}")

            if config.tunnels:
                click.echo(f"  ✓ Created {len(config.tunnels)} tunnel(s)")

            # Test command execution
            result = await transport.execute("paracle --version")
            if result["exit_code"] == 0:
                version = result["stdout"].strip()
                click.echo(f"  ✓ Remote Paracle version: {version}")
            else:
                click.echo("  ⚠ Could not determine remote Paracle version")

        click.echo("\n✓ Connection test successful!")

    except Exception as e:
        click.echo(f"\n✗ Connection test failed: {e}", err=True)
        sys.exit(1)


def _load_remotes_config() -> RemotesConfig:
    """Load remotes configuration from .parac/config/remotes.yaml.

    Returns:
        RemotesConfig: Loaded configuration.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    parac_root = find_parac_root()
    config_path = parac_root / "config" / "remotes.yaml"

    if not config_path.exists():
        return RemotesConfig()

    with open(config_path) as f:
        data = yaml.safe_load(f) or {}

    return RemotesConfig(**data)


def _save_remotes_config(config: RemotesConfig) -> None:
    """Save remotes configuration to .parac/config/remotes.yaml.

    Args:
        config: Configuration to save.
    """
    parac_root = find_parac_root()
    config_dir = parac_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "remotes.yaml"

    with open(config_path, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
