#!/usr/bin/env python3
"""Configuration validation script for FABO run configs."""

import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()


def validate_config(config_path: Path) -> bool:
    """Validate a FABO run configuration file.

    Args:
        config_path: Path to YAML configuration file.

    Returns:
        True if valid, False otherwise.
    """
    console.print(f"[bold]Validating: [cyan]{config_path}[/cyan][/bold]\n")

    # Check file exists
    if not config_path.exists():
        console.print(f"[red]❌ File not found: {config_path}[/red]")
        return False

    # Load YAML
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        console.print(f"[red]❌ Invalid YAML: {e}[/red]")
        return False

    errors = []
    warnings = []

    # Required fields
    required_fields = ["id", "platform", "target", "metrics"]
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Validate ID
    if "id" in config:
        if not isinstance(config["id"], str):
            errors.append("'id' must be a string")
        elif len(config["id"]) < 3:
            errors.append("'id' must be at least 3 characters")
        elif " " in config["id"]:
            warnings.append("'id' should not contain spaces (use hyphens instead)")

    # Validate platform
    if "platform" in config:
        valid_platforms = ["github", "twitter", "linkedin", "youtube", "instagram"]
        if config["platform"] not in valid_platforms:
            errors.append(
                f"Invalid platform '{config['platform']}'. "
                f"Must be one of: {', '.join(valid_platforms)}"
            )

    # Validate target
    if "target" in config:
        if not isinstance(config["target"], dict):
            errors.append("'target' must be a dictionary")
        else:
            platform = config.get("platform")
            if platform == "github":
                if "owner" not in config["target"] or "repo" not in config["target"]:
                    errors.append("GitHub target requires 'owner' and 'repo'")
            elif platform == "twitter":
                if "username" not in config["target"]:
                    errors.append("Twitter target requires 'username'")
            elif platform == "linkedin":
                if "profile_url" not in config["target"] and "username" not in config["target"]:
                    warnings.append("LinkedIn target should have 'profile_url' or 'username'")

    # Validate metrics
    if "metrics" in config:
        if not isinstance(config["metrics"], list):
            errors.append("'metrics' must be a list")
        elif len(config["metrics"]) == 0:
            errors.append("At least one metric must be defined")
        else:
            for i, metric in enumerate(config["metrics"]):
                if not isinstance(metric, dict):
                    errors.append(f"Metric {i} must be a dictionary")
                    continue

                if "type" not in metric:
                    errors.append(f"Metric {i} missing 'type'")

                if "thresholds" not in metric:
                    errors.append(f"Metric {i} missing 'thresholds'")
                elif not isinstance(metric["thresholds"], list):
                    errors.append(f"Metric {i} 'thresholds' must be a list")
                elif len(metric["thresholds"]) == 0:
                    warnings.append(f"Metric {i} has no thresholds defined")
                else:
                    # Check thresholds are sorted
                    thresholds = metric["thresholds"]
                    if thresholds != sorted(thresholds):
                        warnings.append(
                            f"Metric {i} thresholds should be sorted in ascending order"
                        )

    # Validate optimization (optional)
    if "optimization" in config:
        opt = config["optimization"]

        if "api_mode_interval" in opt:
            if not isinstance(opt["api_mode_interval"], int) or opt["api_mode_interval"] <= 0:
                errors.append("'api_mode_interval' must be a positive integer")

        if "screenshot_mode_interval" in opt:
            if (
                not isinstance(opt["screenshot_mode_interval"], int)
                or opt["screenshot_mode_interval"] <= 0
            ):
                errors.append("'screenshot_mode_interval' must be a positive integer")

        if "threshold_proximity_percent" in opt:
            pct = opt["threshold_proximity_percent"]
            if not isinstance(pct, int) or pct < 0 or pct > 100:
                errors.append("'threshold_proximity_percent' must be between 0 and 100")

        if "min_confidence" in opt:
            conf = opt["min_confidence"]
            if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
                errors.append("'min_confidence' must be between 0.0 and 1.0")

        if "mode" in opt:
            valid_modes = ["api", "screenshot", "hybrid", "screenshot_only"]
            if opt["mode"] not in valid_modes:
                errors.append(
                    f"Invalid mode '{opt['mode']}'. "
                    f"Must be one of: {', '.join(valid_modes)}"
                )

    # Display results
    if errors:
        console.print(Panel(
            "\n".join(f"❌ {error}" for error in errors),
            title="[red]Errors[/red]",
            border_style="red",
        ))

    if warnings:
        console.print(Panel(
            "\n".join(f"⚠️  {warning}" for warning in warnings),
            title="[yellow]Warnings[/yellow]",
            border_style="yellow",
        ))

    if not errors and not warnings:
        console.print(Panel(
            "[green]✅ Configuration is valid![/green]",
            border_style="green",
        ))
        return True
    elif not errors:
        console.print(Panel(
            "[yellow]✅ Configuration is valid (with warnings)[/yellow]",
            border_style="yellow",
        ))
        return True
    else:
        console.print(f"\n[red]Found {len(errors)} error(s)[/red]")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: validate-config.py <config-file.yaml>[/yellow]")
        console.print("\nExample:")
        console.print("  python scripts/validate-config.py runs/my-run.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    is_valid = validate_config(config_path)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
