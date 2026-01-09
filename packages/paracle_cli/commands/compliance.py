"""CLI commands for compliance reporting and monitoring."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


@click.group()
def compliance() -> None:
    """Compliance reporting and ISO 42001 monitoring."""
    pass


@compliance.command("report")
@click.option("--since", "-s", default="30d", help="Report period (e.g., '7d', '30d')")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "-f",
    "fmt",
    default="text",
    type=click.Choice(["text", "json", "html"]),
    help="Output format",
)
@click.option("--db", "db_path", help="Path to audit database")
def generate_report(
    since: str,
    output: str | None,
    fmt: str,
    db_path: str | None,
) -> None:
    """Generate compliance report.

    Example: paracle compliance report --since 30d --output report.json
    """
    try:
        from paracle_audit import AuditTrail

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)

        # Parse time period
        now = datetime.utcnow()
        if since.endswith("d"):
            start_time = now - timedelta(days=int(since[:-1]))
        elif since.endswith("h"):
            start_time = now - timedelta(hours=int(since[:-1]))
        else:
            start_time = now - timedelta(days=30)

        report = trail.exporter.generate_compliance_report(
            start_time=start_time,
            end_time=now,
        )

        if fmt == "json":
            report_str = json.dumps(report, indent=2, default=str)
            if output:
                Path(output).write_text(report_str)
                console.print(f"[green]✓[/green] Report saved to {output}")
            else:
                click.echo(report_str)
        elif fmt == "html":
            html = _generate_html_report(report)
            if output:
                Path(output).write_text(html)
                console.print(f"[green]✓[/green] HTML report saved to {output}")
            else:
                click.echo(html)
        else:
            _print_text_report(report)
            if output:
                # Save JSON version
                Path(output).write_text(json.dumps(report, indent=2, default=str))
                console.print(f"\n[dim]Report also saved to {output}[/dim]")

    except ImportError:
        console.print("[red]Error: paracle_audit package not installed[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


def _print_text_report(report: dict) -> None:
    """Print compliance report as formatted text."""
    summary = report.get("summary", {})
    compliance_data = report.get("compliance", {})
    recommendations = report.get("recommendations", [])

    # Header
    console.print(
        Panel(
            f"[bold]Compliance Report[/bold]\n\n"
            f"[dim]Report Time:[/dim] {report.get('report_time', 'N/A')}\n"
            f"[dim]Period:[/dim] {report.get('period', {}).get('start', 'N/A')} to "
            f"{report.get('period', {}).get('end', 'N/A')}\n"
            f"[dim]Total Events:[/dim] {summary.get('total_events', 0)}",
            title="ISO 42001 Compliance",
            border_style="blue",
        )
    )

    # Summary by type
    if summary.get("by_type"):
        console.print("\n[bold]Events by Type:[/bold]")
        table = Table()
        table.add_column("Event Type", style="cyan")
        table.add_column("Count", justify="right")

        for event_type, count in sorted(
            summary["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(event_type, str(count))
        console.print(table)

    # Summary by outcome
    if summary.get("by_outcome"):
        console.print("\n[bold]Events by Outcome:[/bold]")
        table = Table()
        table.add_column("Outcome", style="cyan")
        table.add_column("Count", justify="right")

        outcome_colors = {
            "success": "green",
            "failure": "red",
            "denied": "yellow",
            "pending": "blue",
        }

        for outcome, count in sorted(
            summary["by_outcome"].items(), key=lambda x: x[1], reverse=True
        ):
            color = outcome_colors.get(outcome, "white")
            table.add_row(f"[{color}]{outcome}[/{color}]", str(count))
        console.print(table)

    # ISO Controls
    if summary.get("by_iso_control"):
        console.print("\n[bold]ISO 42001 Controls Triggered:[/bold]")
        for control, count in sorted(summary["by_iso_control"].items()):
            console.print(f"  • Control {control}: {count} events")

    # Compliance issues
    console.print("\n[bold]Compliance Status:[/bold]")

    violations = compliance_data.get("policy_violations_count", 0)
    high_risk = compliance_data.get("high_risk_actions_count", 0)

    if violations == 0 and high_risk < 10:
        console.print("  [green]✓ No significant compliance issues[/green]")
    else:
        if violations > 0:
            console.print(f"  [red]✗ {violations} policy violations[/red]")
        if high_risk >= 10:
            console.print(
                f"  [yellow]⚠ {high_risk} high-risk actions detected[/yellow]"
            )

    # Policy violations details
    if compliance_data.get("policy_violations"):
        console.print("\n[bold red]Policy Violations:[/bold red]")
        for v in compliance_data["policy_violations"][:5]:
            console.print(
                f"  • {v.get('timestamp', 'N/A')}: {v.get('actor')} - {v.get('action')}"
            )
        if len(compliance_data["policy_violations"]) > 5:
            console.print(
                f"  [dim]... and {len(compliance_data['policy_violations']) - 5} more[/dim]"
            )

    # High-risk actions
    if compliance_data.get("high_risk_actions"):
        console.print("\n[bold yellow]High-Risk Actions:[/bold yellow]")
        for a in compliance_data["high_risk_actions"][:5]:
            console.print(
                f"  • {a.get('timestamp', 'N/A')}: {a.get('actor')} - {a.get('action')} "
                f"(risk: {a.get('risk_score', 0):.0f})"
            )
        if len(compliance_data["high_risk_actions"]) > 5:
            console.print(
                f"  [dim]... and {len(compliance_data['high_risk_actions']) - 5} more[/dim]"
            )

    # Recommendations
    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            console.print(f"  • {rec}")


def _generate_html_report(report: dict) -> str:
    """Generate HTML compliance report."""
    summary = report.get("summary", {})
    compliance_data = report.get("compliance", {})
    recommendations = report.get("recommendations", [])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Paracle Compliance Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #1a1a2e; }}
        h2 {{ color: #16213e; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
        th, td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        th {{ background: #f8f9fa; }}
        .recommendation {{ background: #e7f3ff; padding: 12px; margin: 8px 0; border-left: 4px solid #007bff; }}
    </style>
</head>
<body>
    <h1>ISO 42001 Compliance Report</h1>

    <div class="summary">
        <p><strong>Report Time:</strong> {report.get('report_time', 'N/A')}</p>
        <p><strong>Period:</strong> {report.get('period', {}).get('start', 'N/A')} to {report.get('period', {}).get('end', 'N/A')}</p>
        <p><strong>Total Events:</strong> {summary.get('total_events', 0)}</p>
    </div>

    <h2>Events by Type</h2>
    <table>
        <tr><th>Event Type</th><th>Count</th></tr>
"""

    for event_type, count in sorted(
        summary.get("by_type", {}).items(), key=lambda x: x[1], reverse=True
    ):
        html += f"        <tr><td>{event_type}</td><td>{count}</td></tr>\n"

    html += """    </table>

    <h2>Events by Outcome</h2>
    <table>
        <tr><th>Outcome</th><th>Count</th></tr>
"""

    for outcome, count in sorted(
        summary.get("by_outcome", {}).items(), key=lambda x: x[1], reverse=True
    ):
        html += f"        <tr><td>{outcome}</td><td>{count}</td></tr>\n"

    violations = compliance_data.get("policy_violations_count", 0)
    high_risk = compliance_data.get("high_risk_actions_count", 0)

    html += f"""    </table>

    <h2>Compliance Status</h2>
    <p><strong>Policy Violations:</strong> <span class="{'danger' if violations > 0 else 'success'}">{violations}</span></p>
    <p><strong>High-Risk Actions:</strong> <span class="{'warning' if high_risk >= 10 else 'success'}">{high_risk}</span></p>

    <h2>Recommendations</h2>
"""

    for rec in recommendations:
        html += f'    <div class="recommendation">{rec}</div>\n'

    html += """
</body>
</html>"""

    return html


@compliance.command("status")
@click.option("--db", "db_path", help="Path to audit database")
def show_status(db_path: str | None) -> None:
    """Show current compliance status."""
    try:
        from paracle_audit import AuditTrail
        from paracle_governance import PolicyEngine

        trail = AuditTrail(db_path=Path(db_path) if db_path else None)
        engine = PolicyEngine()
        engine.load_default_policies()

        # Get recent stats
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        events_24h = trail.count(start_time=last_24h)
        events_7d = trail.count(start_time=last_7d)

        # Verify integrity
        integrity = trail.verify_integrity()

        # Count policies
        all_policies = engine.list_policies(enabled_only=False)
        enabled_policies_list = engine.list_policies(enabled_only=True)
        policy_count = len(all_policies)
        enabled_policies = len(enabled_policies_list)

        integrity_status = (
            "[green]OK[/green]" if integrity["valid"] else "[red]INVALID[/red]"
        )
        hash_chain = "Enabled" if trail._enable_hash_chain else "Disabled"
        content = (
            "[bold]Compliance Dashboard[/bold]\n\n"
            "[cyan]Audit Trail[/cyan]\n"
            f"  Events (24h): {events_24h}\n"
            f"  Events (7d): {events_7d}\n"
            f"  Integrity: {integrity_status}\n\n"
            "[cyan]Governance[/cyan]\n"
            f"  Policies Loaded: {policy_count}\n"
            f"  Policies Enabled: {enabled_policies}\n\n"
            "[cyan]ISO 42001[/cyan]\n"
            "  Framework: Active\n"
            f"  Hash Chain: {hash_chain}"
        )
        console.print(
            Panel(
                content,
                title="Paracle Compliance Status",
                border_style="green" if integrity["valid"] else "red",
            )
        )

    except ImportError as e:
        console.print(f"[red]Error: Required package not installed: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@compliance.command("controls")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_controls(as_json: bool) -> None:
    """List ISO 42001 controls and their coverage."""
    controls = {
        "4.1": {
            "name": "Understanding the organization and its context",
            "coverage": "Workflow context tracking",
            "status": "partial",
        },
        "4.2": {
            "name": "Understanding the needs and expectations of interested parties",
            "coverage": "Stakeholder policies",
            "status": "partial",
        },
        "5.1": {
            "name": "Leadership and commitment",
            "coverage": "Policy governance",
            "status": "implemented",
        },
        "5.2": {
            "name": "AI Policy",
            "coverage": "Policy engine, default policies",
            "status": "implemented",
        },
        "6.1": {
            "name": "Actions to address risks and opportunities",
            "coverage": "Risk scoring system",
            "status": "implemented",
        },
        "6.2": {
            "name": "AI risk treatment",
            "coverage": "Policy evaluation, approval workflows",
            "status": "implemented",
        },
        "7.2": {
            "name": "Competence",
            "coverage": "Agent capabilities validation",
            "status": "partial",
        },
        "8.1": {
            "name": "Operational planning and control",
            "coverage": "Workflow orchestration",
            "status": "implemented",
        },
        "9.1": {
            "name": "Monitoring, measurement, analysis and evaluation",
            "coverage": "Audit trail, metrics",
            "status": "implemented",
        },
        "9.2": {
            "name": "Internal audit",
            "coverage": "Integrity verification, compliance reports",
            "status": "implemented",
        },
        "10.1": {
            "name": "Nonconformity and corrective action",
            "coverage": "Policy violation tracking",
            "status": "implemented",
        },
    }

    if as_json:
        click.echo(json.dumps(controls, indent=2))
    else:
        console.print("[bold]ISO/IEC 42001 Control Coverage[/bold]\n")

        tree = Tree("[cyan]ISO 42001 Controls[/cyan]")

        for control_id, info in sorted(controls.items()):
            status_icon = {
                "implemented": "[green][OK][/green]",
                "partial": "[yellow][~][/yellow]",
                "planned": "[blue][ ][/blue]",
                "not_started": "[dim][ ][/dim]",
            }.get(info["status"], "[dim][?][/dim]")

            name = info["name"]
            label = f"{status_icon} [bold]{control_id}[/bold]: {name}"
            branch = tree.add(label)
            branch.add(f"[dim]Coverage:[/dim] {info['coverage']}")

        console.print(tree)

        console.print("\n[bold]Legend:[/bold]")
        console.print("  [green][OK][/green] Implemented")
        console.print("  [yellow][~][/yellow] Partial")
        console.print("  [blue][ ][/blue] Planned")


@compliance.command("gaps")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def analyze_gaps(as_json: bool) -> None:
    """Analyze compliance gaps and recommendations."""
    try:
        from paracle_audit import AuditTrail
        from paracle_governance import PolicyEngine

        trail = AuditTrail()
        engine = PolicyEngine()
        engine.load_default_policies()

        gaps = []

        # Check if hash chain is enabled
        if not trail._enable_hash_chain:
            gaps.append(
                {
                    "area": "Audit Integrity",
                    "issue": "Hash chain is disabled",
                    "recommendation": "Enable hash chain for tamper-evident audit trail",
                    "severity": "high",
                    "iso_control": "9.1",
                }
            )

        # Check for default policies only
        all_policies = engine.list_policies(enabled_only=False)
        if len(all_policies) <= 4:
            gaps.append(
                {
                    "area": "Policy Coverage",
                    "issue": "Only default policies are loaded",
                    "recommendation": "Define custom policies for your organization",
                    "severity": "medium",
                    "iso_control": "5.2",
                }
            )

        # Check audit retention
        stats = trail.get_statistics()
        total_events = stats.get("total_events", 0)
        if total_events == 0:
            gaps.append(
                {
                    "area": "Audit Trail",
                    "issue": "No audit events recorded",
                    "recommendation": "Ensure audit hooks are configured for all agent actions",
                    "severity": "high",
                    "iso_control": "9.1",
                }
            )

        # Add generic recommendations if no gaps found
        if not gaps:
            gaps.append(
                {
                    "area": "General",
                    "issue": "No critical gaps detected",
                    "recommendation": "Continue regular compliance monitoring",
                    "severity": "info",
                    "iso_control": "9.2",
                }
            )

        if as_json:
            click.echo(json.dumps(gaps, indent=2))
        else:
            console.print("[bold]Compliance Gap Analysis[/bold]\n")

            for gap in gaps:
                severity_color = {
                    "high": "red",
                    "medium": "yellow",
                    "low": "blue",
                    "info": "green",
                }.get(gap["severity"], "white")

                console.print(
                    Panel(
                        f"[dim]Issue:[/dim] {gap['issue']}\n"
                        f"[dim]Recommendation:[/dim] {gap['recommendation']}\n"
                        f"[dim]ISO Control:[/dim] {gap['iso_control']}",
                        title=f"[{severity_color}]{gap['area']}[/{severity_color}]",
                        border_style=severity_color,
                    )
                )

    except ImportError as e:
        console.print(f"[red]Error: Required package not installed: {e}[/red]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


@compliance.command("export-controls")
@click.argument("output_path", type=click.Path())
@click.option(
    "--format",
    "-f",
    "fmt",
    default="json",
    type=click.Choice(["json", "csv"]),
    help="Output format",
)
def export_controls(output_path: str, fmt: str) -> None:
    """Export ISO 42001 control mapping.

    Example: paracle compliance export-controls ./controls.json
    """
    import csv as csv_module

    controls = {
        "4.1": {"name": "Understanding the organization", "status": "partial"},
        "4.2": {"name": "Understanding stakeholder needs", "status": "partial"},
        "5.1": {"name": "Leadership and commitment", "status": "implemented"},
        "5.2": {"name": "AI Policy", "status": "implemented"},
        "6.1": {"name": "Risk assessment", "status": "implemented"},
        "6.2": {"name": "Risk treatment", "status": "implemented"},
        "7.2": {"name": "Competence", "status": "partial"},
        "8.1": {"name": "Operational control", "status": "implemented"},
        "9.1": {"name": "Monitoring and measurement", "status": "implemented"},
        "9.2": {"name": "Internal audit", "status": "implemented"},
        "10.1": {"name": "Corrective action", "status": "implemented"},
    }

    if fmt == "json":
        Path(output_path).write_text(json.dumps(controls, indent=2))
    else:
        with open(output_path, "w", newline="") as f:
            writer = csv_module.writer(f)
            writer.writerow(["Control ID", "Name", "Status"])
            for control_id, info in sorted(controls.items()):
                writer.writerow([control_id, info["name"], info["status"]])

    console.print(f"[green]✓[/green] Exported to {output_path}")
