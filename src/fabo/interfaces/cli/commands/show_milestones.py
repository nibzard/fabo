"""Show milestones command - view captured milestones."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def show_milestones_command(
    data_dir: str = typer.Option(
        "data",
        "--data-dir",
        "-d",
        help="Data directory path",
    ),
    run_id: str = typer.Option(
        None,
        "--run",
        "-r",
        help="Filter by run ID",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of milestones to show",
    ),
):
    """Show captured milestones.

    Display a list of all milestones that have been captured with
    their screenshots and details.
    """
    console.print("[bold cyan]Captured Milestones 🎉[/bold cyan]\n")

    milestones_dir = Path(data_dir) / "milestones"

    if not milestones_dir.exists():
        console.print("[yellow]No milestones directory found.[/yellow]")
        console.print("Milestones will be saved to:", str(milestones_dir))
        return

    # Find milestone files
    if run_id:
        pattern = f"*-{run_id}.json"
    else:
        pattern = "*.json"

    milestone_files = sorted(milestones_dir.glob(pattern), reverse=True)

    if not milestone_files:
        console.print("[yellow]No milestones captured yet.[/yellow]")
        console.print("\nRun a check to start tracking:")
        console.print("  fabo run --config runs/your-config.yaml")
        return

    # Limit results
    milestone_files = milestone_files[:limit]

    # Create table
    table = Table(title="Captured Milestones")
    table.add_column("Date", style="cyan")
    table.add_column("Time", style="cyan")
    table.add_column("Run ID", style="magenta", no_wrap=True)
    table.add_column("Platform", style="green")
    table.add_column("Metric", style="yellow")
    table.add_column("Value", style="bold yellow")
    table.add_column("Threshold", style="dim")
    table.add_column("Screenshot", style="blue")

    import json
    from datetime import datetime

    for milestone_file in milestone_files:
        try:
            with open(milestone_file, "r") as f:
                milestone = json.load(f)

            # Parse timestamp from filename or data
            timestamp_str = milestone.get("timestamp", "")
            if timestamp_str:
                try:
                    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    date = dt.strftime("%Y-%m-%d")
                    time = dt.strftime("%H:%M:%S")
                except:
                    # Parse from filename
                    date = milestone_file.stem.split("-")[0]
                    time = milestone_file.stem.split("-")[1] if len(milestone_file.stem.split("-")) > 1 else "—"
            else:
                date = "—"
                time = "—"

            run_id_val = milestone.get("run_id", "—")
            platform = milestone.get("platform", "—")
            metric = milestone.get("metric", "—")
            actual_value = milestone.get("actual_value", "—")
            threshold = milestone.get("threshold", "—")

            screenshot_path = milestone.get("screenshot_path")
            screenshot = "✅" if screenshot_path else "—"

            table.add_row(
                date,
                time,
                run_id_val,
                platform,
                metric,
                str(actual_value),
                str(threshold),
                screenshot,
            )

        except Exception as e:
            console.print(f"[red]Error loading {milestone_file}: {e}[/red]")

    console.print(table)
    console.print()

    # Summary
    total_milestones = len(list(milestones_dir.glob("*.json")))
    console.print(f"[dim]Showing {len(milestone_files)} of {total_milestones} milestone(s)[/dim]")

    if len(milestone_files) < total_milestones:
        console.print(f"[dim]Use --limit to show more[/dim]")
