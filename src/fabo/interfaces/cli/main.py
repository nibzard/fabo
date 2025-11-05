"""Main CLI application entry point.

This module provides the command-line interface for FABO using Typer.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fabo.interfaces.cli.commands.run import run_command
from fabo.interfaces.cli.commands.list_runs import list_runs_command
from fabo.interfaces.cli.commands.show_milestones import show_milestones_command
from fabo.interfaces.cli.commands.status import status_command

app = typer.Typer(
    name="fabo",
    help="📸 FABO - Fabulous screen-shooter of your social media milestones",
    add_completion=False,
)

console = Console()

# Register commands
app.command(name="run", help="Run a milestone tracking configuration")(run_command)
app.command(name="runs", help="List all configured tracking runs")(list_runs_command)
app.command(name="milestones", help="Show captured milestones")(show_milestones_command)
app.command(name="status", help="Show FABO status and statistics")(status_command)


@app.command()
def version():
    """Display FABO version information."""
    from importlib.metadata import version as get_version

    try:
        version_str = get_version("fabo")
    except Exception:
        version_str = "0.1.0 (development)"

    console.print(
        Panel(
            f"[bold cyan]FABO[/bold cyan] version [yellow]{version_str}[/yellow]\n"
            f"Fabulous screen-shooter of your social media milestones\n\n"
            f"[dim]Built with Python 3.12+, Steel.dev, and ❤️[/dim]",
            title="📸 FABO",
            border_style="cyan",
        )
    )


@app.command()
def check(
    platform: str = typer.Option(
        None,
        "--platform",
        "-p",
        help="Specific platform to check (github, twitter, linkedin)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force check even if recently checked",
    ),
):
    """Check for new milestones across configured platforms.

    This command checks all enabled platforms (or a specific platform if specified)
    for new milestones and captures screenshots when milestones are reached.
    """
    console.print("[bold cyan]Checking for milestones...[/bold cyan]\n")

    if platform:
        console.print(f"Platform: [yellow]{platform}[/yellow]")

    # TODO: Implement actual checking logic
    console.print("[yellow]⚠ Not yet implemented - coming soon![/yellow]")
    console.print("\nThis command will:")
    console.print("  • Check all enabled platforms for new milestones")
    console.print("  • Capture screenshots when milestones are reached")
    console.print("  • Send notifications about new achievements")


@app.command()
def configure(
    platform: str = typer.Argument(
        ...,
        help="Platform to configure (github, twitter, linkedin)",
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i/-n",
        help="Use interactive configuration wizard",
    ),
):
    """Configure a platform for milestone tracking.

    This command guides you through setting up credentials and thresholds
    for a social media platform.
    """
    console.print(f"[bold cyan]Configuring {platform}...[/bold cyan]\n")

    # TODO: Implement configuration logic
    console.print("[yellow]⚠ Not yet implemented - coming soon![/yellow]")
    console.print("\nThis command will help you:")
    console.print("  • Set up API credentials")
    console.print("  • Configure milestone thresholds")
    console.print("  • Set check frequency")
    console.print("  • Test the connection")


@app.command()
def list(
    platform: str = typer.Option(
        None,
        "--platform",
        "-p",
        help="Filter by platform",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Number of milestones to show",
    ),
):
    """List captured milestones.

    Display a table of all captured milestones with their screenshots.
    """
    console.print("[bold cyan]Recent Milestones[/bold cyan]\n")

    # TODO: Implement listing logic
    # For now, show example table
    table = Table(title="Captured Milestones")
    table.add_column("Date", style="cyan")
    table.add_column("Platform", style="magenta")
    table.add_column("Milestone", style="green")
    table.add_column("Value", style="yellow")
    table.add_column("Screenshot", style="blue")

    # Example row
    table.add_row(
        "2025-11-05",
        "GitHub",
        "Stars",
        "1,000",
        "✅ Captured",
    )

    console.print(table)
    console.print("\n[yellow]⚠ Showing example data - database integration coming soon![/yellow]")


@app.command()
def schedule(
    enable: bool = typer.Option(
        None,
        "--enable/--disable",
        help="Enable or disable the scheduler",
    ),
    interval: int = typer.Option(
        None,
        "--interval",
        "-i",
        help="Default check interval in seconds",
    ),
):
    """Manage the automatic milestone checking schedule.

    Configure the scheduler to automatically check for milestones
    at regular intervals.
    """
    console.print("[bold cyan]Scheduler Configuration[/bold cyan]\n")

    if enable is not None:
        status = "enabled" if enable else "disabled"
        console.print(f"Scheduler: [yellow]{status}[/yellow]")

    if interval:
        console.print(f"Check interval: [yellow]{interval}s[/yellow]")

    # TODO: Implement scheduler management
    console.print("\n[yellow]⚠ Not yet implemented - coming soon![/yellow]")
    console.print("\nThe scheduler will:")
    console.print("  • Run automatic checks at configured intervals")
    console.print("  • Respect platform-specific check frequencies")
    console.print("  • Support cron-like scheduling")


@app.command()
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="API server host",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="API server port",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload for development",
    ),
):
    """Start the FABO API server.

    Launches the REST API server for programmatic access to FABO.
    """
    console.print(
        Panel(
            f"[bold cyan]Starting FABO API Server[/bold cyan]\n\n"
            f"Host: [yellow]{host}[/yellow]\n"
            f"Port: [yellow]{port}[/yellow]\n"
            f"Reload: [yellow]{reload}[/yellow]\n\n"
            f"[dim]API documentation will be available at:[/dim]\n"
            f"  • http://{host}:{port}/docs\n"
            f"  • http://{host}:{port}/redoc",
            border_style="cyan",
        )
    )

    # TODO: Implement API server launch
    console.print("\n[yellow]⚠ Not yet implemented - coming soon![/yellow]")


@app.command()
def status():
    """Show FABO status and configuration.

    Display current configuration, enabled platforms, and system status.
    """
    console.print("[bold cyan]FABO Status[/bold cyan]\n")

    # Configuration status
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="yellow")

    config_table.add_row("Environment", "Development")
    config_table.add_row("Database", "sqlite:///fabo.db")
    config_table.add_row("Screenshots Path", "./screenshots")

    console.print(config_table)
    console.print()

    # Platforms status
    platforms_table = Table(title="Platforms")
    platforms_table.add_column("Platform", style="magenta")
    platforms_table.add_column("Status", style="green")
    platforms_table.add_column("Last Check", style="cyan")

    platforms_table.add_row("GitHub", "✅ Configured", "Never")
    platforms_table.add_row("Twitter", "⚠️  Not configured", "-")
    platforms_table.add_row("LinkedIn", "⚠️  Not configured", "-")

    console.print(platforms_table)

    console.print("\n[yellow]⚠ Showing example data - full implementation coming soon![/yellow]")


@app.command()
def init():
    """Initialize FABO configuration.

    Creates initial configuration files and directory structure.
    """
    console.print("[bold cyan]Initializing FABO...[/bold cyan]\n")

    # TODO: Implement initialization logic
    console.print("[yellow]⚠ Not yet implemented - coming soon![/yellow]")
    console.print("\nThis command will:")
    console.print("  • Create configuration files (.env, config.yaml)")
    console.print("  • Set up screenshot storage directory")
    console.print("  • Initialize database")
    console.print("  • Generate example configuration")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
