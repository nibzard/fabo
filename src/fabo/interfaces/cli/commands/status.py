"""Status command - show overall FABO status."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def status_command(
    data_dir: str = typer.Option(
        "data",
        "--data-dir",
        "-d",
        help="Data directory path",
    ),
):
    """Show FABO status and statistics.

    Display an overview of all runs, milestones, and costs.
    """
    console.print()

    # Load environment info
    import os

    steel_configured = bool(os.getenv("STEEL_API_KEY"))
    anthropic_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    github_configured = bool(os.getenv("GITHUB_TOKEN"))

    # Configuration status
    config_table = Table(title="🔧 Configuration", show_header=False)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Status", style="yellow")

    config_table.add_row("Steel.dev API", "✅ Configured" if steel_configured else "⚠️  Not configured")
    config_table.add_row(
        "LLM API",
        "✅ Configured" if (anthropic_configured or openai_configured) else "⚠️  Not configured"
    )
    if anthropic_configured:
        config_table.add_row("  └─ Anthropic", "✅")
    if openai_configured:
        config_table.add_row("  └─ OpenAI", "✅")

    config_table.add_row("GitHub Token", "✅ Configured" if github_configured else "⚠️  Not configured")
    config_table.add_row("Data Directory", str(data_dir))

    console.print(config_table)
    console.print()

    # Runs status
    runs_dir = Path("runs")
    state_dir = Path(data_dir) / "runs"

    if runs_dir.exists():
        config_files = list(runs_dir.glob("*.yaml")) + list(runs_dir.glob("*.yml"))
        enabled_count = 0
        disabled_count = 0

        import yaml

        for config_file in config_files:
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                if config.get("enabled", True):
                    enabled_count += 1
                else:
                    disabled_count += 1
            except:
                pass

        runs_table = Table(title="📊 Tracking Runs", show_header=False)
        runs_table.add_column("Metric", style="cyan")
        runs_table.add_column("Value", style="yellow")

        runs_table.add_row("Total Runs", str(len(config_files)))
        runs_table.add_row("Enabled", str(enabled_count))
        runs_table.add_row("Disabled", str(disabled_count))

        # Count total checks across all states
        total_checks = 0
        total_api_calls = 0
        total_screenshots = 0

        if state_dir.exists():
            import json

            for state_file in state_dir.glob("*.json"):
                try:
                    with open(state_file, "r") as f:
                        state = json.load(f)
                    total_checks += state.get("total_checks", 0)
                    total_api_calls += state.get("api_calls_made", 0)
                    total_screenshots += state.get("screenshots_taken", 0)
                except:
                    pass

        runs_table.add_row("Total Checks", str(total_checks))
        runs_table.add_row("API Calls", str(total_api_calls))
        runs_table.add_row("Screenshots", str(total_screenshots))

        console.print(runs_table)
        console.print()

    # Milestones
    milestones_dir = Path(data_dir) / "milestones"
    milestone_count = 0

    if milestones_dir.exists():
        milestone_count = len(list(milestones_dir.glob("*.json")))

    milestones_table = Table(title="🎉 Milestones", show_header=False)
    milestones_table.add_column("Metric", style="cyan")
    milestones_table.add_column("Value", style="yellow")

    milestones_table.add_row("Total Captured", str(milestone_count))

    console.print(milestones_table)
    console.print()

    # Cost estimate
    api_cost = 0.0  # Free
    screenshot_cost = total_screenshots * 0.05  # ~$0.05 per screenshot
    llm_cost = total_screenshots * 0.01  # ~$0.01 per LLM call (approximate)
    total_cost = api_cost + screenshot_cost + llm_cost

    cost_table = Table(title="💰 Estimated Costs", show_header=False)
    cost_table.add_column("Service", style="cyan")
    cost_table.add_column("Cost", style="yellow")

    cost_table.add_row("API Calls", f"${api_cost:.2f}")
    cost_table.add_row("Screenshots", f"${screenshot_cost:.2f}")
    cost_table.add_row("LLM Vision", f"${llm_cost:.2f}")
    cost_table.add_row("Total", f"[bold]${total_cost:.2f}[/bold]")

    console.print(cost_table)
    console.print()

    # Quick start hints
    if not config_files:
        console.print(Panel(
            "[yellow]No runs configured yet![/yellow]\n\n"
            "Get started:\n"
            "  1. Copy example: [cyan]cp runs/example-github-stars.yaml runs/my-run.yaml[/cyan]\n"
            "  2. Edit config: [cyan]nano runs/my-run.yaml[/cyan]\n"
            "  3. Run: [cyan]fabo run --config runs/my-run.yaml[/cyan]",
            title="🚀 Quick Start",
            border_style="cyan"
        ))

    if not steel_configured or not (anthropic_configured or openai_configured):
        console.print(Panel(
            "[yellow]Missing API keys for screenshot mode[/yellow]\n\n"
            "Required for screenshot + LLM validation:\n"
            "  • [cyan]STEEL_API_KEY[/cyan] - Get from https://steel.dev\n"
            "  • [cyan]ANTHROPIC_API_KEY[/cyan] or [cyan]OPENAI_API_KEY[/cyan]\n\n"
            "Add to .env file",
            title="⚠️  Configuration",
            border_style="yellow"
        ))
