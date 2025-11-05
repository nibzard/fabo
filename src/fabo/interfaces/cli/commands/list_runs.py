"""List runs command - view configured tracking runs."""

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def list_runs_command(
    data_dir: str = typer.Option(
        "data",
        "--data-dir",
        "-d",
        help="Data directory path",
    ),
    show_disabled: bool = typer.Option(
        False,
        "--show-disabled",
        help="Show disabled runs",
    ),
):
    """List all configured tracking runs.

    Shows current state, progress, and statistics for each run.
    """
    console.print("[bold cyan]Configured FABO Runs[/bold cyan]\n")

    runs_dir = Path("runs")
    state_dir = Path(data_dir) / "runs"

    if not runs_dir.exists():
        console.print("[yellow]No runs directory found. Create 'runs/' directory first.[/yellow]")
        return

    # Find all run configuration files
    config_files = list(runs_dir.glob("*.yaml")) + list(runs_dir.glob("*.yml"))

    if not config_files:
        console.print("[yellow]No run configurations found in 'runs/' directory.[/yellow]")
        console.print("\nCreate a run configuration:")
        console.print("  fabo run --config runs/example-github-stars.yaml")
        return

    # Create table
    table = Table(title="FABO Tracking Runs")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Platform", style="magenta")
    table.add_column("Metric", style="green")
    table.add_column("Current", style="yellow")
    table.add_column("Target", style="yellow")
    table.add_column("Progress", style="blue")
    table.add_column("Mode", style="white")
    table.add_column("Checks", style="dim")
    table.add_column("Status", style="green")

    for config_file in sorted(config_files):
        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            run_id = config.get("id", config_file.stem)
            enabled = config.get("enabled", True)

            if not enabled and not show_disabled:
                continue

            # Load state if exists
            state_file = state_dir / f"{run_id}.json"
            current_value = "—"
            next_threshold = "—"
            progress = "—"
            mode = "—"
            checks = "—"

            if state_file.exists():
                import json

                with open(state_file, "r") as f:
                    state = json.load(f)

                current_value = str(state.get("current_value", "—"))
                next_threshold = str(state.get("next_threshold", "—"))
                mode = state.get("mode", "—")
                checks = str(state.get("total_checks", 0))

                # Calculate progress
                if state.get("current_value") and state.get("next_threshold"):
                    cv = state["current_value"]
                    nt = state["next_threshold"]
                    # Find previous threshold
                    thresholds = sorted(state.get("thresholds", []))
                    prev = 0
                    for t in thresholds:
                        if t < nt:
                            prev = t
                    if nt > prev:
                        pct = ((cv - prev) / (nt - prev)) * 100
                        progress = f"{pct:.0f}%"

            platform = config.get("platform", "—")
            metrics = config.get("metrics", [])
            metric_name = metrics[0].get("type", "—") if metrics else "—"

            status = "✅ Enabled" if enabled else "⚠️ Disabled"

            table.add_row(
                run_id,
                platform,
                metric_name,
                current_value,
                next_threshold,
                progress,
                mode,
                checks,
                status,
            )

        except Exception as e:
            console.print(f"[red]Error loading {config_file}: {e}[/red]")

    console.print(table)
    console.print()

    # Summary
    console.print(f"[dim]Found {len(config_files)} run configuration(s)[/dim]")
    console.print(f"[dim]Data directory: {data_dir}/[/dim]")
