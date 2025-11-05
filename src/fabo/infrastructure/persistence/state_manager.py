"""State manager for persisting operator state between runs.

This module handles loading and saving operator state to enable
continuous monitoring across multiple independent executions.
"""

import json
from pathlib import Path
from typing import Any

import structlog

from fabo.domain.entities.operator_state import OperatorState
from fabo.domain.entities.run_config import RunConfig

logger = structlog.get_logger(__name__)


class StateManager:
    """Manages operator state persistence.

    State can be stored:
    - Locally in JSON files
    - In Git repository (for GitHub Actions)
    - In database (for production)
    """

    def __init__(self, data_dir: Path = Path("data")):
        """Initialize state manager.

        Args:
            data_dir: Base directory for state storage.
        """
        self.data_dir = Path(data_dir)
        self.runs_dir = self.data_dir / "runs"
        self.milestones_dir = self.data_dir / "milestones"
        self.logger = logger.bind(service="state_manager")

        # Ensure directories exist
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.milestones_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self, run_config: RunConfig) -> OperatorState:
        """Load state for a run configuration.

        Args:
            run_config: Run configuration.

        Returns:
            Loaded state or new state if not found.
        """
        state_path = self.data_dir / run_config.get_state_file_path()

        if state_path.exists():
            self.logger.info("loading_state", run_id=run_config.id, path=str(state_path))

            try:
                with open(state_path, "r") as f:
                    data = json.load(f)

                # Convert ISO datetime strings back to datetime objects
                from datetime import datetime

                for field in ["last_check", "created_at", "updated_at"]:
                    if field in data and isinstance(data[field], str):
                        data[field] = datetime.fromisoformat(data[field])

                state = OperatorState(**data)
                self.logger.info("state_loaded", run_id=run_config.id, checks=state.total_checks)
                return state

            except Exception as e:
                self.logger.error(
                    "failed_to_load_state", run_id=run_config.id, error=str(e)
                )
                # Fall through to create new state

        # Create new state
        self.logger.info("creating_new_state", run_id=run_config.id)
        return self._create_initial_state(run_config)

    def save_state(self, state: OperatorState) -> None:
        """Save state to disk.

        Args:
            state: Operator state to save.
        """
        state_path = self.data_dir / "runs" / f"{state.run_id}.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info("saving_state", run_id=state.run_id, path=str(state_path))

        # Convert to dict and handle datetime serialization
        data = state.model_dump(mode="json")

        # Save with pretty formatting for Git-friendliness
        with open(state_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        self.logger.info("state_saved", run_id=state.run_id)

    def save_milestone(self, milestone_data: dict[str, Any], run_id: str) -> Path:
        """Save milestone data.

        Args:
            milestone_data: Milestone data to save.
            run_id: Run identifier.

        Returns:
            Path to saved milestone file.
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{run_id}.json"
        milestone_path = self.milestones_dir / filename

        self.logger.info("saving_milestone", run_id=run_id, path=str(milestone_path))

        with open(milestone_path, "w") as f:
            json.dump(milestone_data, f, indent=2, default=str)

        return milestone_path

    def list_states(self) -> list[str]:
        """List all available run states.

        Returns:
            List of run IDs with saved states.
        """
        return [p.stem for p in self.runs_dir.glob("*.json")]

    def list_milestones(self, run_id: str | None = None) -> list[Path]:
        """List milestone files.

        Args:
            run_id: Optional run ID to filter by.

        Returns:
            List of milestone file paths.
        """
        if run_id:
            pattern = f"*-{run_id}.json"
        else:
            pattern = "*.json"

        return sorted(self.milestones_dir.glob(pattern), reverse=True)

    def _create_initial_state(self, run_config: RunConfig) -> OperatorState:
        """Create initial state from run configuration.

        Args:
            run_config: Run configuration.

        Returns:
            New operator state.
        """
        primary_metric = run_config.get_primary_metric()

        # Determine initial mode
        if run_config.optimization.mode:
            mode = run_config.optimization.mode
        else:
            from fabo.domain.entities.operator_state import OperatorMode

            mode = OperatorMode.API  # Start in API mode

        # Find next threshold
        next_threshold = min(primary_metric.thresholds) if primary_metric.thresholds else None

        state = OperatorState(
            run_id=run_config.id,
            platform=run_config.platform.value,
            target=run_config.target,
            metric_name=primary_metric.type,
            thresholds=sorted(primary_metric.thresholds),
            next_threshold=next_threshold,
            mode=mode,
            api_mode_interval=run_config.optimization.api_mode_interval,
            screenshot_mode_interval=run_config.optimization.screenshot_mode_interval,
            threshold_proximity_percent=run_config.optimization.threshold_proximity_percent,
        )

        return state

    def cleanup_old_states(self, keep_count: int = 10) -> int:
        """Clean up old state files, keeping only the most recent.

        Args:
            keep_count: Number of states to keep per run.

        Returns:
            Number of files deleted.
        """
        # Group by run ID
        states_by_run: dict[str, list[Path]] = {}

        for state_file in self.runs_dir.glob("*.json"):
            run_id = state_file.stem
            if run_id not in states_by_run:
                states_by_run[run_id] = []
            states_by_run[run_id].append(state_file)

        deleted = 0
        for run_id, files in states_by_run.items():
            # Sort by modification time
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Delete old files
            for old_file in files[keep_count:]:
                old_file.unlink()
                deleted += 1
                self.logger.info("deleted_old_state", run_id=run_id, path=str(old_file))

        return deleted
