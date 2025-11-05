"""Platform domain entity.

This module defines the Platform entity which represents a configured
social media platform to monitor for milestones.
"""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fabo.domain.value_objects.milestone_type import MilestoneType, PlatformType
from fabo.domain.value_objects.platform_credentials import PlatformCredentials


class Platform(BaseModel):
    """Represents a configured social media platform.

    This entity contains all configuration for monitoring a specific platform,
    including credentials, thresholds, and check frequency.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique platform configuration ID")
    platform_type: PlatformType = Field(..., description="Type of platform")
    name: str = Field(..., description="User-defined name for this configuration")
    enabled: bool = Field(True, description="Whether monitoring is enabled")
    credentials: PlatformCredentials = Field(..., description="Platform credentials")
    check_interval_seconds: int = Field(
        3600, gt=0, description="How often to check for milestones (in seconds)"
    )
    milestone_thresholds: dict[MilestoneType, list[int]] = Field(
        default_factory=dict,
        description="Threshold values to monitor for each milestone type",
    )
    target_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific configuration (e.g., repo owner/name for GitHub)",
    )
    last_check_values: dict[MilestoneType, int] = Field(
        default_factory=dict,
        description="Last known values for each metric",
    )

    class Config:
        """Pydantic model configuration."""

        frozen = False  # Allow updates for last_check_values, enabled, etc.

    def has_valid_credentials(self) -> bool:
        """Check if platform has valid credentials configured.

        Returns:
            True if credentials are present.
        """
        return self.credentials.has_credentials()

    def get_thresholds_for_type(self, milestone_type: MilestoneType) -> list[int]:
        """Get threshold values for a specific milestone type.

        Args:
            milestone_type: The type of milestone to get thresholds for.

        Returns:
            List of threshold values, empty if none configured.
        """
        return self.milestone_thresholds.get(milestone_type, [])

    def get_next_threshold(self, milestone_type: MilestoneType, current_value: int) -> int | None:
        """Get the next threshold value to reach for a milestone type.

        Args:
            milestone_type: The type of milestone.
            current_value: The current value of the metric.

        Returns:
            The next threshold value, or None if all thresholds have been reached.
        """
        thresholds = sorted(self.get_thresholds_for_type(milestone_type))
        for threshold in thresholds:
            if current_value < threshold:
                return threshold
        return None

    def update_last_check_value(self, milestone_type: MilestoneType, value: int) -> None:
        """Update the last known value for a milestone type.

        Args:
            milestone_type: The type of milestone.
            value: The current value.
        """
        self.last_check_values[milestone_type] = value

    def get_last_check_value(self, milestone_type: MilestoneType) -> int:
        """Get the last known value for a milestone type.

        Args:
            milestone_type: The type of milestone.

        Returns:
            The last known value, or 0 if never checked.
        """
        return self.last_check_values.get(milestone_type, 0)

    def __str__(self) -> str:
        """Return string representation of the platform."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({self.platform_type.value}) - {status}"
