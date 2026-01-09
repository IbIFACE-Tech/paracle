"""CLI commands for audit trail management."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def audit() -> None:
    """Manage audit trails and compliance logging."""
    pass


@audit.command("search")
@click.option("--actor", "-a", help="Filter by actor")
@click.option("--type", "-t", "event_type", help="Filter by event type")
@click.option("--outcome", "-o", help="Filter by outcome (success, failure, denied)")
@click.option("--since", "-s", help="Events since (e.g., '1h', '24h', '7d')")
@click.option("--limit", "-l", default=50, help="Maximum events to return")
@click.option("--db", "db_path", help="Path to audit database")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_events(
    actor: str | None,
    event_type: str | None,
    outcome: str | None,
    since: str | None,
    limit: int,
    db_path: str | None,
    as_json: bool,
) -> None:
    """Search audit events with filters.

    Example: paracle audit search --actor coder --since 24h
    """
    try:
        from paracle_audit import AuditEventType, AuditOutcome, AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)

        # Parse since
        start_time = None
        if since:
            now = datetime.utcnow()
            if since.endswith("h"):
                hours = int(since[:-1])
                start_time = now - timedelta(hours=hours)
            elif since.endswith("d"):
                days = int(since[:-1])
                start_time = now - timedelta(days=days)
            elif since.endswith("m"):
                minutes = int(since[:-1])
                start_time = now - timedelta(minutes=minutes)

        # Parse event type
        event_type_filter = None
        if event_type:
            try:
                event_type_filter = AuditEventType(event_type.lower())
            except ValueError:
                # Try uppercase
                try:
                    event_type_filter = AuditEventType[event_type.upper()]
                except KeyError:
                    console.print(
                        f"[yellow]Warning: Unknown event type '{event_type}'[/yellow]"
                    )

        # Parse outcome
        outcome_filter = None
        if outcome:
            try:
                outcome_filter = AuditOutcome(outcome.lower())
            except ValueError:
                console.print(f"[yellow]Warning: Unknown outcome '{outcome}'[/yellow]")

        events = trail.query(
            actor=actor,
            event_type=event_type_filter,
            outcome=outcome_filter,
            start_time=start_time,
            limit=limit,
        )

        if as_json:
            click.echo(json.dumps([e.to_dict() for e in events], indent=2, default=str))
        else:
            if not events:
                console.print("[yellow]No events found[/yellow]")
                return

            table = Table(title=f"Audit Events ({len(events)} results)")
            table.add_column("Time", style="dim", no_wrap=True)
            table.add_column("Type", style="cyan")
            table.add_column("Actor", style="blue")
            table.add_column("Action", style="white")
            table.add_column("Target", style="magenta")
            table.add_column("Outcome", style="green")

            for e in events:
                # Color outcome
                outcome_color = {
                    "success": "green",
                    "failure": "red",
                    "denied": "yellow",
                    "pending": "blue",
                    "error": "red bold",
                }.get(e.outcome.value, "white")

                table.add_row(
                    e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    e.event_type.value,
                    e.actor,
                    e.action[:30],
                    (e.target or "-")[:25],
                    f"[{outcome_color}]{e.outcome.value}[/{outcome_color}]",
                )

            console.print(table)

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@audit.command("show")
@click.argument("event_id")
@click.option("--db", "db_path", help="Path to audit database")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_event(event_id: str, db_path: str | None, as_json: bool) -> None:
    """Show details of a specific audit event."""
    try:
        from paracle_audit import AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)
        event = trail.get(event_id)

        if not event:
            console.print(f"[red]Error: Event '{event_id}' not found[/red]")
            raise SystemExit(1)

        if as_json:
            click.echo(json.dumps(event.to_dict(), indent=2, default=str))
        else:
            console.print(
                Panel(
                    f"[dim]Event ID:[/dim] {event.event_id}\n"
                    f"[dim]Type:[/dim] {event.event_type.value}\n"
                    f"[dim]Timestamp:[/dim] {event.timestamp.isoformat()}\n"
                    f"[dim]Actor:[/dim] {event.actor} ({event.actor_type})\n"
                    f"[dim]Action:[/dim] {event.action}\n"
                    f"[dim]Target:[/dim] {event.target or '(none)'}\n"
                    f"[dim]Outcome:[/dim] {event.outcome.value}\n"
                    f"[dim]Risk Score:[/dim] {event.risk_score or 'N/A'}\n"
                    f"[dim]Risk Level:[/dim] {event.risk_level or 'N/A'}\n"
                    f"[dim]Policy ID:[/dim] {event.policy_id or 'N/A'}\n"
                    f"[dim]ISO Control:[/dim] {event.iso_control or 'N/A'}",
                    title="Audit Event Details",
                )
            )

            if event.context:
                console.print("\n[bold]Context:[/bold]")
                for key, value in event.context.items():
                    console.print(f"  {key}: {value}")

            if event.event_hash:
                console.print(f"\n[dim]Hash:[/dim] {event.event_hash[:32]}...")
                if event.previous_hash:
                    console.print(
                        f"[dim]Previous Hash:[/dim] {event.previous_hash[:32]}..."
                    )

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@audit.command("export")
@click.argument("output_path", type=click.Path())
@click.option(
    "--format",
    "-f",
    "fmt",
    default="json",
    type=click.Choice(["json", "csv", "jsonl", "syslog"]),
    help="Export format",
)
@click.option("--actor", "-a", help="Filter by actor")
@click.option("--type", "-t", "event_type", help="Filter by event type")
@click.option("--since", "-s", help="Events since (e.g., '1h', '24h', '7d')")
@click.option("--until", "-u", "until_time", help="Events until")
@click.option("--limit", "-l", type=int, help="Maximum events to export")
@click.option("--db", "db_path", help="Path to audit database")
def export_events(
    output_path: str,
    fmt: str,
    actor: str | None,
    event_type: str | None,
    since: str | None,
    until_time: str | None,
    limit: int | None,
    db_path: str | None,
) -> None:
    """Export audit events to a file.

    Example: paracle audit export ./audit_report.json --format json --since 7d
    """
    try:
        from paracle_audit import AuditEventType, AuditTrail, ExportFormat

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)

        # Parse times
        start_time = None
        end_time = None
        now = datetime.utcnow()

        if since:
            if since.endswith("h"):
                start_time = now - timedelta(hours=int(since[:-1]))
            elif since.endswith("d"):
                start_time = now - timedelta(days=int(since[:-1]))

        if until_time:
            try:
                end_time = datetime.fromisoformat(until_time)
            except ValueError:
                console.print(
                    f"[yellow]Warning: Could not parse until time '{until_time}'[/yellow]"
                )

        # Parse event type
        event_type_filter = None
        if event_type:
            try:
                event_type_filter = AuditEventType(event_type.lower())
            except ValueError:
                try:
                    event_type_filter = AuditEventType[event_type.upper()]
                except KeyError:
                    pass

        # Map format
        format_map = {
            "json": ExportFormat.JSON,
            "csv": ExportFormat.CSV,
            "jsonl": ExportFormat.JSONL,
            "syslog": ExportFormat.SYSLOG,
        }
        export_format = format_map[fmt]

        count = trail.export(
            output_path,
            format=export_format,
            actor=actor,
            event_type=event_type_filter,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        console.print(f"[green]✓[/green] Exported {count} events to {output_path}")

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@audit.command("verify")
@click.option("--db", "db_path", help="Path to audit database")
@click.option("--max-events", "-m", default=10000, help="Maximum events to verify")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def verify_integrity(db_path: str | None, max_events: int, as_json: bool) -> None:
    """Verify audit trail integrity (hash chain).

    Example: paracle audit verify --db ./audit.db
    """
    try:
        from paracle_audit import AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)
        result = trail.verifier.verify_chain(max_events=max_events)

        if as_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            if result["valid"]:
                console.print("[green]✓ Audit trail integrity verified[/green]")
            else:
                console.print("[red]✗ Integrity violation detected![/red]")
                console.print(
                    f"[dim]Violation at:[/dim] {result.get('violation_event')}"
                )
                console.print(f"[dim]Type:[/dim] {result.get('violation_type')}")

            console.print(f"\n[dim]Events verified:[/dim] {result['events_verified']}")
            if result.get("first_event_id"):
                console.print(
                    f"[dim]First event:[/dim] {result['first_event_id'][:16]}..."
                )
            if result.get("last_event_id"):
                console.print(
                    f"[dim]Last event:[/dim] {result['last_event_id'][:16]}..."
                )

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@audit.command("stats")
@click.option("--db", "db_path", help="Path to audit database")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def show_stats(db_path: str | None, as_json: bool) -> None:
    """Show audit trail statistics."""
    try:
        from paracle_audit import AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)
        stats = trail.get_statistics()

        if as_json:
            click.echo(json.dumps(stats, indent=2, default=str))
        else:
            console.print(
                Panel(
                    f"[dim]Total Events:[/dim] {stats.get('total_events', 0)}\n"
                    f"[dim]Hash Chain Enabled:[/dim] {stats.get('hash_chain_enabled', True)}\n"
                    f"[dim]Event Hooks:[/dim] {stats.get('event_hooks_count', 0)}\n"
                    f"[dim]Earliest Event:[/dim] {stats.get('earliest_event', 'N/A')}\n"
                    f"[dim]Latest Event:[/dim] {stats.get('latest_event', 'N/A')}",
                    title="Audit Statistics",
                )
            )

            if stats.get("by_type"):
                console.print("\n[bold]Events by Type:[/bold]")
                for event_type, count in sorted(
                    stats["by_type"].items(), key=lambda x: x[1], reverse=True
                ):
                    bar = "█" * min(count, 30)
                    console.print(f"  {event_type:25} {bar} {count}")

            if stats.get("by_outcome"):
                console.print("\n[bold]Events by Outcome:[/bold]")
                for outcome, count in sorted(
                    stats["by_outcome"].items(), key=lambda x: x[1], reverse=True
                ):
                    bar = "█" * min(count, 30)
                    console.print(f"  {outcome:15} {bar} {count}")

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@audit.command("retention")
@click.argument("days", type=int)
@click.option("--archive", "-a", type=click.Path(), help="Archive path before deletion")
@click.option("--db", "db_path", help="Path to audit database")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def apply_retention(
    days: int, archive: str | None, db_path: str | None, yes: bool
) -> None:
    """Apply retention policy (delete old events).

    Example: paracle audit retention 90 --archive ./archive.jsonl
    """
    try:
        from paracle_audit import AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)

        # Get count of events that will be deleted
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = trail.count(end_time=cutoff)

        if count == 0:
            console.print(f"[yellow]No events older than {days} days[/yellow]")
            return

        if not yes:
            console.print(
                f"[yellow]This will delete {count} events older than {days} days[/yellow]"
            )
            if archive:
                console.print(f"[dim]Events will be archived to: {archive}[/dim]")
            if not click.confirm("Proceed?"):
                console.print("[dim]Cancelled[/dim]")
                return

        result = trail.apply_retention_policy(
            retention_days=days,
            archive_path=Path(archive) if archive else None,
        )

        console.print(f"[green]✓[/green] Deleted {result['deleted_count']} events")
        if result.get("archived_path"):
            console.print(f"[dim]Archived to:[/dim] {result['archived_path']}")
            console.print(
                f"[dim]Archived count:[/dim] {result.get('archived_count', 'N/A')}"
            )

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@audit.command("report")
@click.option("--since", "-s", help="Report period start (e.g., '7d', '30d')")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--db", "db_path", help="Path to audit database")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def generate_report(
    since: str | None,
    output: str | None,
    db_path: str | None,
    as_json: bool,
) -> None:
    """Generate integrity report.

    Example: paracle audit report --since 30d --output report.json
    """
    try:
        from paracle_audit import AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)
        report = trail.generate_integrity_report()

        if output:
            with open(output, "w") as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"[green]✓[/green] Report saved to {output}")
        elif as_json:
            click.echo(json.dumps(report, indent=2, default=str))
        else:
            console.print(
                Panel(
                    f"[dim]Verification Time:[/dim] {report['verification_time']}\n"
                    f"[dim]Total Events:[/dim] {report['total_events']}\n"
                    f"[dim]Events Verified:[/dim] {report['events_verified']}\n"
                    f"[dim]Chain Valid:[/dim] {'✓ Yes' if report['chain_valid'] else '✗ No'}\n"
                    f"[dim]Violations:[/dim] {report['violations_count']}",
                    title="Integrity Report",
                )
            )

            if report.get("violations"):
                console.print("\n[red][bold]Violations Found:[/bold][/red]")
                for v in report["violations"][:10]:
                    console.print(f"  • {v['event_id'][:16]}: {v['violation_type']}")

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)
