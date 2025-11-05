"""Run configuration entity for operator executions.

This defines a tracking run configuration that can be executed
independently via cron, GitHub Actions, or manual CLI.
"""

from typing import Any

from pydantic import BaseModel, Field

from fabo.domain.entities.operator_state import OperatorMode
from fabo.domain.value_objects.milestone_type import PlatformType


class MetricConfig(BaseModel):
    """Configuration for a specific metric to track."""

    type: str = Field(..., description="Metric type (stars, followers, etc)")
    thresholds: list[int] = Field(..., description="Threshold values to monitor")


class OptimizationConfig(BaseModel):
    """Optimization settings for the run."""

    mode: OperatorMode | None = Field(
        None, description="Force specific mode (None for automatic)"
    )
    api_mode_interval: int = Field(
        3600, description="Check interval in API mode (seconds)"
    )
    screenshot_mode_interval: int = Field(
        300, description="Check interval in screenshot mode (seconds)"
    )
    threshold_proximity_percent: int = Field(
        90, ge=0, le=100, description="Proximity % to switch modes"
    )
    min_confidence: float = Field(
        0.85, ge=0.0, le=1.0, description="Minimum LLM confidence to accept"
    )
    max_retries: int = Field(
        3, ge=1, description="Max retries for low confidence"
    )


class NotificationConfig(BaseModel):
    """Notification settings for milestones."""

    enabled: bool = Field(True, description="Enable notifications")
    channels: list[str] = Field(
        default_factory=lambda: ["console"],
        description="Notification channels (console, email, slack, etc)",
    )


class RunConfig(BaseModel):
    """Configuration for a milestone tracking run.

    Each run config defines an independent tracking operation
    that can be executed by operators.
    """

    id: str = Field(..., description="Unique run identifier")
    name: str | None = Field(None, description="Human-readable name")
    description: str | None = Field(None, description="Description of what this run tracks")

    # Platform configuration
    platform: PlatformType = Field(..., description="Platform to monitor")
    target: dict[str, Any] = Field(
        ..., description="Platform-specific target (repo, username, etc)"
    )

    # Metrics to track
    metrics: list[MetricConfig] = Field(..., description="Metrics to track")

    # Optimization
    optimization: OptimizationConfig = Field(
        default_factory=OptimizationConfig,
        description="Optimization settings",
    )

    # Notifications
    notifications: NotificationConfig = Field(
        default_factory=NotificationConfig,
        description="Notification settings",
    )

    # State persistence
    state_file: str | None = Field(
        None, description="Path to state file (relative to data dir)"
    )

    # Metadata
    enabled: bool = Field(True, description="Whether this run is enabled")
    tags: list[str] = Field(default_factory=list, description="Tags for organization")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        """Pydantic configuration."""

        frozen = True  # Run configs are immutable

    def get_state_file_path(self) -> str:
        """Get the state file path for this run.

        Returns:
            Path to state file.
        """
        if self.state_file:
            return self.state_file
        return f"data/runs/{self.id}.json"

    def get_primary_metric(self) -> MetricConfig:
        """Get the primary (first) metric configuration.

        Returns:
            Primary metric config.

        Raises:
            ValueError: If no metrics are configured.
        """
        if not self.metrics:
            raise ValueError(f"No metrics configured for run {self.id}")
        return self.metrics[0]

    def __str__(self) -> str:
        """String representation."""
        return f"RunConfig({self.id}: {self.platform.value}/{self.get_primary_metric().type})"
