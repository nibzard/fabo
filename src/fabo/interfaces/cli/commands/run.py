"""Run command for executing standalone operator checks.

This module provides the CLI command for running operator checks,
designed to be executed via cron, GitHub Actions, or manual invocation.
"""

import asyncio
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fabo.domain.entities.run_config import RunConfig
from fabo.infrastructure.config.settings import get_settings
from fabo.infrastructure.llm.vision_service import VisionService
from fabo.infrastructure.operators.factory import create_operator
from fabo.infrastructure.operators.smart_operator import SmartOperator
from fabo.infrastructure.persistence.state_manager import StateManager
from fabo.infrastructure.screenshot.screenshot_service import ScreenshotService
from fabo.infrastructure.screenshot.steel_client import SteelClient

console = Console()


def run_command(
    config: str = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to run configuration YAML file",
    ),
    mode: str = typer.Option(
        None,
        "--mode",
        "-m",
        help="Force specific mode (api, screenshot, hybrid)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show what would happen without executing",
    ),
    force_screenshot: bool = typer.Option(
        False,
        "--force-screenshot",
        "-f",
        help="Force screenshot capture regardless of proximity",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output",
    ),
):
    """Execute a milestone tracking run.

    This command runs an independent operator check that can be triggered
    via cron, GitHub Actions, or manually.

    Example:
        fabo run --config runs/github-stars.yaml
        fabo run --config runs/twitter.yaml --mode screenshot
        fabo run --config runs/all.yaml --dry-run
    """
    asyncio.run(_run_async(config, mode, dry_run, force_screenshot, verbose))


async def _run_async(
    config_path: str,
    mode: str | None,
    dry_run: bool,
    force_screenshot: bool,
    verbose: bool,
):
    """Async implementation of run command."""
    console.print(f"[bold cyan]FABO Operator Run[/bold cyan]\n")

    # Load run configuration
    config_file = Path(config_path)
    if not config_file.exists():
        console.print(f"[red]Error: Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)

    console.print(f"Loading configuration: [yellow]{config_path}[/yellow]")

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    # Convert to RunConfig
    from fabo.domain.value_objects.milestone_type import PlatformType

    config_data["platform"] = PlatformType(config_data["platform"])
    run_config = RunConfig(**config_data)

    console.print(f"Run ID: [yellow]{run_config.id}[/yellow]")
    console.print(f"Platform: [yellow]{run_config.platform.value}[/yellow]")
    console.print(f"Target: [yellow]{run_config.target}[/yellow]\n")

    if not run_config.enabled:
        console.print("[yellow]⚠️  Run is disabled in configuration[/yellow]")
        return

    if dry_run:
        console.print("[yellow]Dry run mode - no actual checks will be performed[/yellow]\n")

    # Initialize services
    settings = get_settings()

    # State manager
    state_manager = StateManager(data_dir=Path("data"))

    # Load or create state
    state = state_manager.load_state(run_config)

    console.print(f"Current state:")
    console.print(f"  Mode: [cyan]{state.mode.value}[/cyan]")
    console.print(f"  Current value: [cyan]{state.current_value or 'Unknown'}[/cyan]")
    console.print(f"  Next threshold: [cyan]{state.next_threshold}[/cyan]")
    console.print(f"  Proximity: [cyan]{state.calculate_proximity():.1f}%[/cyan]")
    console.print(f"  Total checks: [cyan]{state.total_checks}[/cyan]")
    console.print(f"  API calls: [cyan]{state.api_calls_made}[/cyan]")
    console.print(f"  Screenshots: [cyan]{state.screenshots_taken}[/cyan]\n")

    # Override mode if specified
    if mode:
        from fabo.domain.entities.operator_state import OperatorMode

        state.mode = OperatorMode(mode.lower())
        console.print(f"Mode overridden to: [yellow]{mode}[/yellow]\n")

    if force_screenshot:
        from fabo.domain.entities.operator_state import OperatorMode

        state.mode = OperatorMode.SCREENSHOT
        console.print("[yellow]Forcing screenshot mode[/yellow]\n")

    if dry_run:
        console.print("[green]Dry run complete - no changes made[/green]")
        return

    # Initialize platform operator
    from fabo.domain.entities.platform import Platform
    from fabo.domain.value_objects.platform_credentials import PlatformCredentials

    # Create platform config for operator
    credentials = PlatformCredentials(
        platform=run_config.platform.value,
        api_key=_get_api_key(run_config.platform.value, settings),
        bearer_token=_get_bearer_token(run_config.platform.value, settings),
    )

    platform_config = Platform(
        platform_type=run_config.platform,
        name=run_config.id,
        credentials=credentials,
        target_config=run_config.target,
        milestone_thresholds={},  # Not used in smart operator
    )

    base_operator = create_operator(platform_config)

    # Initialize services
    steel_client = SteelClient(api_key=settings.steel_api_key)
    screenshot_service = ScreenshotService(
        steel_client=steel_client,
        screenshots_dir=settings.screenshots_path,
    )

    # Determine LLM provider
    llm_api_key = _get_llm_api_key(settings)
    vision_service = VisionService(
        provider="anthropic",  # Default to Anthropic
        api_key=llm_api_key,
    )

    # Create smart operator
    smart_operator = SmartOperator(
        base_operator=base_operator,
        run_config=run_config,
        state=state,
        screenshot_service=screenshot_service,
        vision_service=vision_service,
    )

    # Execute check
    console.print("[bold]Executing check...[/bold]\n")

    try:
        result = await smart_operator.execute_check()

        # Display results
        table = Table(title="Check Results")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Mode Used", result["mode_used"])
        table.add_row(
            "Current Value",
            str(result["current_value"]) if result["current_value"] else "N/A",
        )
        table.add_row("Milestone Reached", "✅ Yes" if result["milestone_reached"] else "No")

        if result.get("confidence"):
            table.add_row("Confidence", f"{result['confidence']:.2%}")

        if result.get("screenshot_path"):
            table.add_row("Screenshot", result["screenshot_path"])

        if result.get("error"):
            table.add_row("Error", result["error"])

        console.print(table)
        console.print()

        # Get updated state
        updated_state = smart_operator.get_state()

        # Display state summary
        console.print("[bold]Updated State:[/bold]")
        console.print(updated_state.get_summary())
        console.print()

        # Display cost estimate
        costs = updated_state.get_cost_estimate()
        console.print("[bold]Estimated Costs:[/bold]")
        console.print(f"  API calls: ${costs['api_calls']:.2f}")
        console.print(f"  Screenshots: ${costs['screenshots']:.2f}")
        console.print(f"  LLM vision: ${costs['llm_vision']:.2f}")
        console.print(f"  Total: [yellow]${costs['total']:.2f}[/yellow]")
        console.print()

        # Save state
        state_manager.save_state(updated_state)
        console.print("[green]✅ State saved successfully[/green]")

        # If milestone reached, save milestone data
        if result["milestone_reached"]:
            milestone_data = {
                "run_id": run_config.id,
                "platform": run_config.platform.value,
                "metric": state.metric_name,
                "threshold": state.next_threshold,
                "actual_value": result["current_value"],
                "screenshot_path": result.get("screenshot_path"),
                "timestamp": updated_state.last_check.isoformat(),
                "confidence": result.get("confidence"),
            }

            milestone_path = state_manager.save_milestone(milestone_data, run_config.id)
            console.print(f"[green]🎉 Milestone saved: {milestone_path}[/green]")

            # Advance to next threshold
            updated_state.advance_to_next_threshold()
            state_manager.save_state(updated_state)

    except Exception as e:
        console.print(f"[red]Error during check: {e}[/red]")
        raise typer.Exit(1)

    finally:
        # Cleanup
        await base_operator.close()
        await steel_client.close()
        await vision_service.close()


def _get_api_key(platform: str, settings) -> str | None:
    """Get API key for platform."""
    if platform == "github":
        return settings.github_token
    return None


def _get_bearer_token(platform: str, settings) -> str | None:
    """Get bearer token for platform."""
    if platform == "twitter":
        return settings.twitter_bearer_token
    elif platform == "linkedin":
        return settings.linkedin_access_token
    return None


def _get_llm_api_key(settings) -> str:
    """Get LLM API key."""
    # Try to get from environment
    import os

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        return anthropic_key

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return openai_key

    raise ValueError(
        "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable."
    )
